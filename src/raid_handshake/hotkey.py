from __future__ import annotations

import ctypes
import sys
import threading
from collections.abc import Callable


class GlobalHotkey:
    """Optional Windows Ctrl+Shift+Enter; no keyboard recording or hooks."""

    def __init__(self):
        self.active = False
        self.error: str | None = None
        self.thread: threading.Thread | None = None
        self.thread_id: int | None = None

    def start(self, callback: Callable[[], None]) -> None:
        if sys.platform != "win32":
            self.error = "Global hotkey is available on Windows; the send button still works."
            return
        self.thread = threading.Thread(
            target=self._listen, args=(callback,), daemon=True, name="raid-send-hotkey"
        )
        self.thread.start()

    def _listen(self, callback: Callable[[], None]) -> None:
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, 7301, 0x4000 | 0x0002 | 0x0004, 0x0D):
            self.error = "Ctrl+Shift+Enter is in use by another application. Use the send button."
            return
        self.active = True
        message = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == 0x0312:
                    callback()
        finally:
            user32.UnregisterHotKey(None, 7301)
            self.active = False

    def stop(self) -> None:
        if sys.platform == "win32" and self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
        if self.thread:
            self.thread.join(timeout=1)
