from __future__ import annotations

import asyncio
import hashlib
import secrets
import time
import uuid
from collections import OrderedDict, deque
from datetime import datetime
from typing import Any

import httpx
from openai import APIError

from .ai import Context, OpenAIContext
from .audio import AudioCapture
from .config import ChannelConfig, ConfigStore, Settings
from .credentials import Credentials
from .hotkey import GlobalHotkey
from .learning import WaveLearner
from .metrics import Metrics
from .models import LandingDraft, RaidRun, StreamSummary
from .storage import Store
from .twitch import Twitch, TwitchError


def stamp(value: str | None, fallback: float) -> float:
    if not value:
        return fallback
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (ValueError, OverflowError):
        return fallback


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Service:
    def __init__(self, settings: Settings, credentials: Credentials | None = None):
        self.settings = settings
        self.config_store = ConfigStore(settings.data_dir)
        self.config = self.config_store.load()
        if not self.config.twitch_client_id and settings.twitch_client_id:
            self.config.twitch_client_id = settings.twitch_client_id.strip()
        self.credentials = credentials or Credentials()
        if settings.openai_api_key and not self.credentials.get("openai_api_key"):
            self.credentials.set("openai_api_key", settings.openai_api_key.get_secret_value())
        self.twitch = Twitch(self.config.twitch_client_id, self.credentials)
        self.ai = OpenAIContext(self.credentials)
        self.store = Store(settings.data_dir)
        self.metrics = Metrics(self.config.chatters_poll_seconds)
        self.context = Context()
        self.summary: StreamSummary | None = None
        self.summary_error: str | None = None
        self.summary_running = False
        self.summary_lock = asyncio.Lock()
        self.send_lock = asyncio.Lock()
        self.audio = AudioCapture()
        self.audio_queue: asyncio.Queue[tuple[bytes, float]] = asyncio.Queue(maxsize=3)
        self.audio_requested = False
        self.transcription_error: str | None = None
        self.hotkey = GlobalHotkey()
        self.drafts: dict[str, LandingDraft] = {}
        self.learners: dict[str, WaveLearner] = {}
        self.tasks: set[asyncio.Task] = set()
        self.seen: OrderedDict[str, float] = OrderedDict()
        self.activity: deque[dict] = deque(maxlen=30)
        self.admin_token = secrets.token_urlsafe(32)
        self.overlay_token = self.credentials.get("overlay_token") or secrets.token_urlsafe(32)
        self.credentials.set("overlay_token", self.overlay_token)
        self.eventsub_status = "waiting"
        self.eventsub_error: str | None = None
        self.chatters_error: str | None = None
        self.chatters_status = "waiting"
        self._event_gap: float | None = None
        self._owner: str | None = None
        self._last_summary_attempt = 0.0
        self._subscribers: set[asyncio.Queue] = set()
        self._dirty = True
        self.closed = False

    def _spawn(self, coroutine, name: str) -> asyncio.Task:
        task = asyncio.create_task(coroutine, name=name)
        self.tasks.add(task)

        def done(finished: asyncio.Task) -> None:
            self.tasks.discard(finished)
            if not finished.cancelled() and finished.exception():
                self.note("task_error", f"{name} stopped; check connection health.")

        task.add_done_callback(done)
        return task

    def note(self, kind: str, message: str) -> None:
        self.activity.appendleft({"at": time.time(), "kind": kind, "message": message})
        self._dirty = True
        self.notify()

    def notify(self) -> None:
        """Push critical cards immediately; the timer only drives countdowns/telemetry."""
        for queue in list(self._subscribers):
            if not queue.full():
                queue.put_nowait(True)

    async def start(self) -> None:
        now = time.time()
        raids, drafts = self.store.load(now)
        self.metrics.raids = raids
        self.drafts = {draft.id: draft for draft in drafts}
        self.seen.update((raid.id, now) for raid in raids)
        if raids:
            self.metrics.gap(min(raid.started_at for raid in raids), now)
            for raid in raids:
                if not raid.cohort_finalized:
                    raid.cohort_complete = False
                if raid.learning.get("status") == "learning":
                    raid.learning = {
                        "status": "insufficient",
                        "messages": 0,
                        "note": "Collection interrupted by an application restart.",
                    }
        await self.twitch.restore()
        self._spawn(self.twitch.run_events(self.on_event, self.on_health), "twitch-eventsub")
        self._spawn(self._poll_loop(), "chatter-polling")
        self._spawn(self._tick_loop(), "live-updates")
        self._spawn(self._summary_loop(), "rolling-summary")
        self._spawn(self._transcription_loop(), "openai-transcription")
        if self.config.global_hotkey:
            loop = asyncio.get_running_loop()
            self.hotkey.start(
                lambda: loop.call_soon_threadsafe(
                    lambda: self._spawn(self.send_latest(), "hotkey-send")
                )
            )

    async def close(self) -> None:
        self.closed = True
        self.audio_requested = False
        self.hotkey.stop()
        await asyncio.to_thread(self.audio.stop)
        tasks = list(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.persist()
        await self.twitch.close()
        await self.ai.close()
        self.store.close()

    def on_health(self, status: str, error: str | None) -> None:
        if self.eventsub_status == "connected" and status != "connected":
            self._event_gap = time.time()
            self.metrics.gap(self._event_gap, float("inf"))
        if status == "connected" and self._event_gap is not None:
            self.metrics.event_gaps = [
                (a, time.time() if b == float("inf") else b) for a, b in self.metrics.event_gaps
            ]
            self._event_gap = None
        if status != self.eventsub_status:
            self.note("eventsub", f"EventSub {status}.")
        self.eventsub_status, self.eventsub_error = status, error
        self._dirty = True

    def _sync_owner(self) -> None:
        if not self.twitch.user:
            return
        uid = self.twitch.user["id"]
        if uid == self._owner:
            return
        if self._owner is not None:
            self.metrics = Metrics(self.config.chatters_poll_seconds)
            self.drafts.clear()
            self.learners.clear()
            self.context = Context()
            self.summary = None
        self.metrics.raids = [raid for raid in self.metrics.raids if raid.target_id == uid]
        allowed = {raid.id for raid in self.metrics.raids}
        self.drafts = {key: draft for key, draft in self.drafts.items() if draft.raid_id in allowed}
        self.metrics.snapshots.clear()
        self._owner = uid
        self.note("connected", f"Receiving channel: {self.twitch.user['display_name']}.")

    async def _poll_loop(self) -> None:
        while True:
            if self.twitch.user:
                self._sync_owner()
                try:
                    if time.time() - self.twitch.validated_at > 3600:
                        await self.twitch.validate()
                    snapshot = await self.twitch.chatters()
                    self.metrics.observe(snapshot)
                    self.chatters_status, self.chatters_error = "connected", None
                    self.persist()
                except (httpx.HTTPError, TwitchError, ValueError, KeyError):
                    self.chatters_status = "error"
                    self.chatters_error = (
                        "Chatter polling failed. No partial/zero snapshot was recorded."
                    )
                    self.metrics.failed_poll(time.time())
                self._dirty = True
            await asyncio.sleep(self.config.chatters_poll_seconds)

    async def on_event(self, packet: dict) -> None:
        now = time.time()
        metadata = packet["metadata"]
        message_id = metadata["message_id"]
        if message_id in self.seen:
            return
        self.seen[message_id] = now
        while self.seen and (len(self.seen) > 20000 or next(iter(self.seen.values())) < now - 3600):
            self.seen.popitem(last=False)
        self._sync_owner()
        payload = packet["payload"]
        event = payload["event"]
        kind = payload["subscription"]["type"]
        when = stamp(metadata.get("message_timestamp"), now)
        if kind == "channel.raid":
            raid = RaidRun(
                id=message_id,
                started_at=when,
                received_at=now,
                source_id=event["from_broadcaster_user_id"],
                source_login=event["from_broadcaster_user_login"],
                source_name=event["from_broadcaster_user_name"],
                viewers=event["viewers"],
                target_id=event["to_broadcaster_user_id"],
            )
            raid.guest.name, raid.guest.login = raid.source_name, raid.source_login
            self.metrics.begin(raid)
            self.learners[raid.id] = WaveLearner(raid.source_id)
            self.store.save_raid(raid)
            self.note(
                "raid", f"Real raid received from {raid.source_name}: {raid.viewers} participants."
            )
            self._spawn(self._guest_context(raid), f"guest-{raid.id}")
            self._spawn(self._landing(raid), f"landing-{raid.id}")
        elif kind == "channel.chat.message":
            uid = event["chatter_user_id"]
            text = event.get("message", {}).get("text", "")
            ordinary = event.get("message_type", "text") == "text"
            is_self = self.twitch.user and uid == self.twitch.user["id"]
            is_app_message = is_self and any(
                draft.text == text
                and draft.status in {"sending", "sent", "uncertain"}
                and abs(now - draft.created_at) < 120
                for draft in self.drafts.values()
            )
            self.metrics.add_message(when, uid, ordinary and not is_app_message)
            if ordinary and not is_self:
                self.context.add_chat(when, text)
            for raid in self.metrics.raids:
                if raid.started_at <= when <= raid.started_at + 60 and raid.id in self.learners:
                    if not is_self:
                        self.learners[raid.id].add(event)
                        raid.learning = self.learners[raid.id].result()
        elif kind == "channel.follow":
            self.metrics.add_follow(stamp(event.get("followed_at"), when), message_id)
        self._dirty = True

    async def _guest_context(self, raid: RaidRun) -> None:
        try:
            raid.guest = await asyncio.wait_for(
                self.twitch.guest(raid.source_id, raid.source_login, raid.source_name), 4.5
            )
        except (TimeoutError, httpx.HTTPError, TwitchError, KeyError, ValueError):
            raid.guest.error = "Source lookup timed out; available raid facts are shown."
        self.store.save_raid(raid)
        self._dirty = True
        self.notify()

    async def refresh_summary(self, force: bool = False) -> StreamSummary | None:
        async with self.summary_lock:
            now = time.time()
            if not self.credentials.get("openai_api_key"):
                self.summary_error = "Add your OpenAI API key."
                return None
            window = self.context.window(now, self.config.transcript_window_seconds)
            if not window["transcript"]:
                self.summary_error = "Waiting for real audio transcription."
                return None
            if (
                not force
                and self.summary
                and self.summary.window_end >= window["transcript"][-1][0]
            ):
                return self.summary
            self.summary_running = True
            self._last_summary_attempt = now
            self._dirty = True
            try:
                self.summary = await self.ai.summarize(self.context, self.config, now)
                self.summary_error = None
            except APIError as exc:
                self.summary_error = (
                    f"OpenAI summary request failed ({getattr(exc, 'status_code', 'network')})."
                )
            except (ValueError, TimeoutError):
                self.summary_error = (
                    "Summary unavailable: check transcript freshness and model access."
                )
            finally:
                self.summary_running = False
                self._dirty = True
            return self.summary

    async def _summary_loop(self) -> None:
        while True:
            if time.time() - self._last_summary_attempt >= self.config.summary_interval_seconds:
                await self.refresh_summary()
            await asyncio.sleep(2)

    def summary_ready(self) -> bool:
        now = time.time()
        return (
            self.summary is not None
            and now - self.summary.created_at <= 120
            and (now - self.summary.window_end <= 120)
        )

    async def _landing(self, raid: RaidRun) -> None:
        if not self.summary_ready():
            await self.refresh_summary(force=True)
        if not self.summary_ready() or self.summary is None:
            self.note(
                "landing_waiting",
                "Landing card needs a fresh real transcript; start audio capture.",
            )
            return
        try:
            text = self.config.render(self.summary.activity)
        except ValueError:
            self.note("landing_error", "Landing template is too long. Shorten its fixed text.")
            return
        automatic = (
            self.config.preapproved_enabled
            and self.config.approved_template_hash == self.config.template_hash()
        )
        draft = LandingDraft(
            id=uuid.uuid4().hex,
            raid_id=raid.id,
            text=text,
            text_hash=digest(text),
            created_at=time.time(),
            summary_at=self.summary.window_end,
            automatic=automatic,
            template_hash=self.config.template_hash(),
        )
        previous = self.drafts.get(raid.draft_id or "")
        if previous and previous.status not in {"sent", "sending", "uncertain"}:
            previous.status = "expired"
            self.store.save_draft(previous)
        self.drafts[draft.id] = draft
        raid.draft_id = draft.id
        self.store.save_draft(draft)
        self.store.save_raid(raid)
        self._dirty = True
        self.notify()
        if automatic:
            await self.send(draft.id, automatic=True)

    async def rebuild_landing(self, raid_id: str) -> None:
        raid = next((r for r in self.metrics.raids if r.id == raid_id), None)
        if raid is None:
            raise ValueError("Raid is no longer in this session.")
        previous = self.drafts.get(raid.draft_id or "")
        if previous and previous.status in {"sent", "sending", "uncertain"}:
            raise ValueError(
                "This raid already has a sent or unresolved message. Check Twitch first."
            )
        await self._landing(raid)

    def preview(self, draft_id: str, text_hash: str) -> None:
        draft = self.drafts[draft_id]
        if draft.text_hash != text_hash or draft.status not in {"pending", "previewed", "failed"}:
            raise ValueError("The landing card changed or is no longer available.")
        draft.previewed_at, draft.status = time.time(), "previewed"
        self.store.save_draft(draft)
        self._dirty = True
        self.notify()

    async def send_latest(self) -> None:
        candidates = [
            draft
            for draft in self.drafts.values()
            if draft.status in {"pending", "previewed", "failed"}
        ]
        if not candidates:
            self.note("send", "No pending landing card. Wait for a real raid.")
            return
        try:
            await self.send(max(candidates, key=lambda d: d.created_at).id)
        except (ValueError, KeyError) as exc:
            self.note("send", str(exc))

    async def send(self, draft_id: str, automatic: bool = False) -> LandingDraft:
        async with self.send_lock:
            draft = self.drafts[draft_id]
            if draft.status in {"sent", "sending", "uncertain", "expired"}:
                raise ValueError(
                    "This landing card was already sent, expired, or has an unresolved send."
                )
            if any(
                other.id != draft.id
                and other.raid_id == draft.raid_id
                and other.status in {"sent", "sending", "uncertain"}
                for other in self.drafts.values()
            ):
                raise ValueError(
                    "Another message for this raid was already sent or has an unresolved send."
                )
            if time.time() - draft.summary_at > 120:
                draft.status = "expired"
                self.store.save_draft(draft)
                self._dirty = True
                raise ValueError(
                    "The transcript is stale. Regenerate the landing card before sending."
                )
            if automatic:
                if (
                    not self.config.preapproved_enabled
                    or self.config.approved_template_hash != self.config.template_hash()
                    or draft.template_hash != self.config.template_hash()
                ):
                    raise ValueError("Preapproved template mode is not enabled for this template.")
            elif not draft.previewed_at:
                raise ValueError(
                    "Open the control room and preview the complete landing card first."
                )
            draft.status, draft.error = "sending", None
            self.store.save_draft(draft)
            self._dirty = True
            try:
                result = await self.twitch.send_chat(draft.text)
                draft.status, draft.message_id, draft.sent_at = (
                    "sent",
                    result["message_id"],
                    time.time(),
                )
                self.note("sent", "Landing card delivered to Twitch chat.")
            except TwitchError as exc:
                draft.status = "uncertain" if exc.status >= 500 else "failed"
                draft.error = str(exc)
                self.note("send_error", draft.error)
            except (httpx.HTTPError, TimeoutError, KeyError, ValueError):
                draft.status = "uncertain"
                draft.error = (
                    "Delivery outcome unknown. Check Twitch chat; no automatic retry was made."
                )
                self.note("send_error", draft.error)
            self.store.save_draft(draft)
            self._dirty = True
            return draft

    async def start_audio(self) -> None:
        if not self.credentials.get("openai_api_key"):
            raise ValueError("Configure your OpenAI API key first.")
        loop = asyncio.get_running_loop()
        self.audio_requested = True
        self.transcription_error = None

        def incoming(data: bytes, when: float) -> None:
            loop.call_soon_threadsafe(self._queue_audio, data, when)

        try:
            self.audio.start(self.config.audio_device_id, incoming)
        except Exception:
            self.audio_requested = False
            raise
        self.note("audio", "Audio capture started; voiced segments are sent to OpenAI.")

    def _queue_audio(self, data: bytes, when: float) -> None:
        if not self.audio_requested:
            return
        try:
            self.audio_queue.put_nowait((data, when))
        except asyncio.QueueFull:
            self.transcription_error = (
                "Transcription is falling behind; an audio segment was dropped."
            )
        self._dirty = True

    async def stop_audio(self) -> None:
        self.audio_requested = False
        await asyncio.to_thread(self.audio.stop)
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()
        self.note("audio", "Audio capture stopped.")

    async def _transcription_loop(self) -> None:
        while True:
            wav, when = await self.audio_queue.get()
            if not self.audio_requested:
                continue
            try:
                text = await self.ai.transcribe(wav, self.config)
                self.context.add_transcript(when, text)
                self.transcription_error = None
            except APIError as exc:
                self.transcription_error = (
                    f"OpenAI transcription failed ({getattr(exc, 'status_code', 'network')})."
                )
            except (ValueError, TimeoutError):
                self.transcription_error = (
                    "OpenAI transcription unavailable. Check key and model access."
                )
            self._dirty = True

    async def _tick_loop(self) -> None:
        while True:
            now = time.time()
            if self.metrics.advance(now):
                self.persist()
            for raid in self.metrics.raids:
                if raid.id in self.learners and now >= raid.started_at + 60:
                    raid.learning = self.learners.pop(raid.id).result(final=True)
                    self.store.save_raid(raid)
            self.context.window(now, self.config.transcript_window_seconds)
            self.store.prune(now)
            live_ids = {raid.id for raid in self.metrics.raids}
            self.drafts = {
                key: draft for key, draft in self.drafts.items() if draft.raid_id in live_ids
            }
            for queue in list(self._subscribers):
                if not queue.full():
                    queue.put_nowait(True)
            self._dirty = False
            await asyncio.sleep(1)

    def persist(self) -> None:
        for raid in self.metrics.raids:
            self.store.save_raid(raid)

    def update_config(self, values: dict[str, Any], approve_template: bool = False) -> None:
        previous = self.config
        candidate = ChannelConfig.model_validate(dict(previous.model_dump(), **values))
        if self.twitch.user and candidate.twitch_client_id != previous.twitch_client_id:
            raise ValueError("Disconnect Twitch before changing the Client ID.")
        changed_template = candidate.template_hash() != previous.template_hash()
        if approve_template:
            candidate.approved_template_hash = candidate.template_hash()
        elif changed_template:
            candidate.preapproved_enabled = False
            candidate.approved_template_hash = ""
        if (
            candidate.preapproved_enabled
            and candidate.approved_template_hash != candidate.template_hash()
        ):
            raise ValueError("Confirm the template before enabling automatic sending.")
        self.config_store.save(candidate)
        self.config = candidate
        self.twitch.client_id = candidate.twitch_client_id
        self.metrics.poll_seconds = candidate.chatters_poll_seconds
        self._dirty = True

    def state(self, overlay: bool = False) -> dict:
        now = time.time()
        raids = [raid.public() for raid in reversed(self.metrics.raids)]
        if overlay:
            latest = self.metrics.raids[-1] if self.metrics.raids else None
            draft = self.drafts.get(latest.draft_id or "") if latest else None
            return {
                "now": now,
                "raids": raids[:1],
                "channel": self.twitch.user.get("display_name") if self.twitch.user else None,
                "landing": draft.text if draft and draft.status == "sent" else None,
                "eventsub": self.eventsub_status,
            }
        snapshot = self.metrics.latest
        return {
            "now": now,
            "config": self.config.model_dump(exclude={"approved_template_hash"}),
            "template_hash": self.config.template_hash(),
            "user": self.twitch.user,
            "device_login": self.twitch.device,
            "login_error": self.twitch.login_error,
            "health": {
                "eventsub": self.eventsub_status,
                "eventsub_error": self.eventsub_error,
                "chatters": self.chatters_status,
                "chatters_error": self.chatters_error,
                "baseline_at": snapshot.observed_at if snapshot else None,
                "chatters_count": len(snapshot.users) if snapshot else None,
                "openai_configured": bool(self.credentials.get("openai_api_key")),
                "credential_storage": self.credentials.storage,
                "global_hotkey": self.hotkey.active,
                "hotkey_error": self.hotkey.error,
            },
            "audio": {
                "active": self.audio.active,
                "level": self.audio.level,
                "error": self.audio.error or self.transcription_error,
                "last_chunk": self.audio.last_chunk,
                "queue": self.audio_queue.qsize(),
            },
            "summary": self.summary.model_dump() if self.summary else None,
            "summary_ready": self.summary_ready(),
            "summary_running": self.summary_running,
            "summary_error": self.summary_error,
            "transcript": [
                {"at": t, "text": text} for t, text in list(self.context.transcript)[-4:]
            ],
            "raids": raids,
            "drafts": [draft.model_dump() for draft in self.drafts.values()][-8:],
            "activity": list(self.activity),
        }
