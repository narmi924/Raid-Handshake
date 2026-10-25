from __future__ import annotations

import io
import threading
import time
import wave
from collections.abc import Callable

import numpy as np


def pcm_wav(samples: np.ndarray, sample_rate: int = 16000) -> bytes:
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(pcm.tobytes())
    return buffer.getvalue()


def devices() -> list[dict]:
    import soundcard as sc

    return [
        {"id": mic.id, "name": mic.name, "loopback": bool(mic.isloopback)}
        for mic in sc.all_microphones(include_loopback=True)
    ]


class AudioCapture:
    def __init__(self):
        self.active = False
        self.error: str | None = None
        self.level = 0.0
        self.last_chunk: float | None = None
        self.thread: threading.Thread | None = None
        self.stop_event = threading.Event()

    def start(self, device_id: str, callback: Callable[[bytes, float], None]) -> None:
        if self.thread and self.thread.is_alive():
            raise ValueError("Audio capture is already running.")
        self.error = None
        self.stop_event.clear()
        self.active = True
        self.thread = threading.Thread(
            target=self._record, args=(device_id, callback), name="raid-audio-capture", daemon=True
        )
        self.thread.start()

    def _record(self, device_id: str, callback: Callable[[bytes, float], None]) -> None:
        try:
            import soundcard as sc

            microphone = (
                sc.get_microphone(device_id, include_loopback=True)
                if device_id
                else sc.default_microphone()
            )
            if microphone is None:
                raise RuntimeError("No audio input is available.")
            # Capture all native channels then downmix, avoiding the WASAPI single-channel bug.
            with microphone.recorder(samplerate=16000) as recorder:
                blocks = []
                for_block = 16000
                while not self.stop_event.is_set():
                    data = recorder.record(numframes=for_block)
                    mono = data.mean(axis=1) if data.ndim > 1 else data
                    self.level = float(np.sqrt(np.mean(mono * mono)))
                    blocks.append(mono)
                    if len(blocks) >= 8:
                        samples = np.concatenate(blocks)
                        blocks.clear()
                        self.last_chunk = time.time()
                        # Silence is not uploaded, avoiding transcription hallucinations and waste.
                        if float(np.sqrt(np.mean(samples * samples))) >= 0.003:
                            callback(pcm_wav(samples), self.last_chunk)
        except Exception:
            self.error = (
                "Audio capture failed. Check the selected device and Windows microphone permission."
            )
        finally:
            self.active = False
            self.level = 0.0

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
        self.active = False
