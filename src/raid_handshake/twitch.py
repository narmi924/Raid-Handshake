from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from .credentials import Credentials
from .models import ChatSnapshot, GuestContext

SCOPES = (
    "user:read:chat",
    "user:write:chat",
    "moderator:read:chatters",
    "moderator:read:followers",
)
HELIX = "https://api.twitch.tv/helix"
OAUTH = "https://id.twitch.tv/oauth2"
EVENTSUB = "wss://eventsub.wss.twitch.tv/ws?keepalive_timeout_seconds=30"


class TwitchError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


class Twitch:
    def __init__(self, client_id: str, credentials: Credentials):
        self.client_id = client_id
        self.credentials = credentials
        self.http = httpx.AsyncClient(timeout=httpx.Timeout(12, connect=8))
        self.tokens: dict | None = None
        self.user: dict | None = None
        self.device: dict | None = None
        self.login_error: str | None = None
        self.token_lock = asyncio.Lock()
        self.validated_at = 0.0
        self.device_task: asyncio.Task | None = None
        self.socket: object | None = None

    def _save(self) -> None:
        self.credentials.set("twitch_tokens", json.dumps(self.tokens))

    async def restore(self) -> bool:
        stored = self.credentials.get("twitch_tokens")
        if not stored or not self.client_id:
            return False
        try:
            self.tokens = json.loads(stored)
            if self.tokens.get("client_id") != self.client_id:
                self.tokens = None
                return False
            await self.access_token()
            await self.validate()
            return True
        except (ValueError, TwitchError, httpx.HTTPError):
            self.login_error = "Saved Twitch authorization could not be restored. Reconnect Twitch."
            self.tokens = None
            self.user = None
            return False

    async def begin_device(self) -> dict:
        if not self.client_id:
            raise TwitchError("Enter your Twitch Public Client ID first.")
        if self.device_task and not self.device_task.done():
            self.device_task.cancel()
            await asyncio.gather(self.device_task, return_exceptions=True)
        response = await self.http.post(
            f"{OAUTH}/device", data={"client_id": self.client_id, "scopes": " ".join(SCOPES)}
        )
        if response.status_code != 200:
            raise TwitchError(
                "Device login failed. Check that the Client ID is a Public Client.",
                response.status_code,
            )
        data = response.json()
        self.device = {
            "user_code": data["user_code"],
            "verification_uri": data["verification_uri"],
            "expires_at": time.time() + data.get("expires_in", 1800),
            "status": "pending",
        }
        self.login_error = None
        self.device_task = asyncio.create_task(self._poll_device(data), name="twitch-device-login")
        return self.device

    async def _poll_device(self, data: dict) -> None:
        interval = max(5, data.get("interval", 5))
        assert self.device is not None
        deadline = self.device["expires_at"]
        try:
            while time.time() < deadline:
                await asyncio.sleep(interval)
                response = await self.http.post(
                    f"{OAUTH}/token",
                    data={
                        "client_id": self.client_id,
                        "device_code": data["device_code"],
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                )
                body = response.json()
                if response.status_code == 200:
                    self.tokens = dict(
                        body, expires_at=time.time() + body["expires_in"], client_id=self.client_id
                    )
                    self._save()
                    await self.validate()
                    self.device["status"] = "authorized"
                    return
                pending = str(body.get("message", body.get("error", ""))).lower()
                if "authorization_pending" in pending or "authorization pending" in pending:
                    continue
                if "slow_down" in pending:
                    interval += 5
                    continue
                raise TwitchError(
                    "Twitch device authorization was denied or expired.", response.status_code
                )
            raise TwitchError("The device code expired. Start Twitch login again.")
        except (TwitchError, httpx.HTTPError, ValueError, KeyError) as exc:
            self.login_error = str(exc) if isinstance(exc, TwitchError) else "Twitch login failed."
            self.device["status"] = "error"

    async def _refresh(self) -> None:
        if not self.tokens or not self.tokens.get("refresh_token"):
            raise TwitchError("Connect Twitch to continue.", 401)
        response = await self.http.post(
            f"{OAUTH}/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": self.tokens["refresh_token"],
            },
        )
        if response.status_code != 200:
            self.user = None
            raise TwitchError("Twitch authorization expired or was revoked. Reconnect Twitch.", 401)
        body = response.json()
        self.tokens = dict(
            body, expires_at=time.time() + body["expires_in"], client_id=self.client_id
        )
        # Public DCF refresh tokens rotate and are single-use; save the replacement immediately.
        self._save()

    async def access_token(self) -> str:
        async with self.token_lock:
            if not self.tokens:
                raise TwitchError("Connect Twitch to continue.", 401)
            if self.tokens.get("expires_at", 0) <= time.time() + 60:
                await self._refresh()
            assert self.tokens is not None
            return self.tokens["access_token"]

    async def validate(self) -> None:
        token = await self.access_token()
        response = await self.http.get(
            f"{OAUTH}/validate", headers={"Authorization": f"OAuth {token}"}
        )
        if response.status_code == 401:
            async with self.token_lock:
                if self.tokens and self.tokens["access_token"] == token:
                    await self._refresh()
            token = await self.access_token()
            response = await self.http.get(
                f"{OAUTH}/validate", headers={"Authorization": f"OAuth {token}"}
            )
        if response.status_code != 200:
            raise TwitchError("Twitch could not validate the user token.", response.status_code)
        body = response.json()
        if body["client_id"] != self.client_id or not set(SCOPES) <= set(body.get("scopes", [])):
            raise TwitchError("Twitch authorization is missing required scopes. Reconnect Twitch.")
        user = (await self.request("GET", "/users"))["data"][0]
        self.user = {
            key: user.get(key, "") for key in ("id", "login", "display_name", "profile_image_url")
        }
        self.validated_at = time.time()

    async def request(self, method: str, endpoint: str, **kwargs) -> dict:
        token = await self.access_token()
        headers = {"Client-Id": self.client_id, "Authorization": f"Bearer {token}"}
        response = await self.http.request(method, f"{HELIX}{endpoint}", headers=headers, **kwargs)
        if response.status_code == 401:
            async with self.token_lock:
                if self.tokens and self.tokens["access_token"] == token:
                    await self._refresh()
            headers["Authorization"] = f"Bearer {await self.access_token()}"
            response = await self.http.request(
                method, f"{HELIX}{endpoint}", headers=headers, **kwargs
            )
        if response.status_code >= 400:
            raise TwitchError(
                f"Twitch {endpoint}: HTTP {response.status_code}. Check permissions or rate limits.",
                response.status_code,
            )
        return response.json() if response.content else {}

    async def chatters(self) -> ChatSnapshot:
        if not self.user:
            raise TwitchError("The broadcaster has not connected Twitch.")
        users: set[str] = set()
        after = ""
        seen_cursors: set[str] = set()
        for page in range(1, 101):
            params = {
                "broadcaster_id": self.user["id"],
                "moderator_id": self.user["id"],
                "first": 1000,
            }
            if after:
                params["after"] = after
            body = await self.request("GET", "/chat/chatters", params=params)
            users.update(item["user_id"] for item in body["data"])
            after = body.get("pagination", {}).get("cursor", "")
            if not after:
                return ChatSnapshot(observed_at=time.time(), users=users, pages=page)
            if after in seen_cursors:
                raise TwitchError("Chatters pagination repeated; partial results were discarded.")
            seen_cursors.add(after)
        raise TwitchError("Chatters pagination exceeded the limit; partial results were discarded.")

    async def guest(self, source_id: str, login: str, name: str) -> GuestContext:
        context = GuestContext(name=name, login=login)
        since = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        results = await asyncio.gather(
            self.request("GET", "/channels", params={"broadcaster_id": source_id}),
            self.request(
                "GET",
                "/clips",
                params={"broadcaster_id": source_id, "started_at": since, "first": 100},
            ),
            self.request("GET", "/users", params={"id": source_id}),
            return_exceptions=True,
        )
        if isinstance(results[0], dict) and results[0].get("data"):
            info = results[0]["data"][0]
            context.title = info.get("title") or "Unknown"
            context.category = info.get("game_name") or "Unknown"
        else:
            context.error = "Source channel information unavailable"
        if isinstance(results[1], dict):
            candidates = sorted(
                results[1].get("data", []), key=lambda c: c["created_at"], reverse=True
            )
            context.clips = [
                {key: clip.get(key) for key in ("id", "title", "url", "created_at")}
                for clip in candidates[:3]
            ]
        elif isinstance(results[1], Exception):
            context.error = "Some source information is unavailable"
        if isinstance(results[2], dict) and results[2].get("data"):
            context.image = results[2]["data"][0].get("profile_image_url", "")
        return context

    async def send_chat(self, text: str) -> dict:
        if not self.user:
            raise TwitchError("Connect the receiving broadcaster first.")
        if not 1 <= len(text) <= 500:
            raise TwitchError("Chat messages must be between 1 and 500 characters.")
        body = await self.request(
            "POST",
            "/chat/messages",
            json={"broadcaster_id": self.user["id"], "sender_id": self.user["id"], "message": text},
        )
        result = body["data"][0]
        if not result.get("is_sent"):
            reason = result.get("drop_reason") or {}
            raise TwitchError(
                f"Twitch did not send the message: {reason.get('code', 'not permitted')}."
            )
        return result

    async def subscribe(self, session_id: str) -> None:
        assert self.user is not None
        uid = self.user["id"]
        subscriptions = [
            ("channel.raid", "1", {"to_broadcaster_user_id": uid}),
            ("channel.chat.message", "1", {"broadcaster_user_id": uid, "user_id": uid}),
            ("channel.follow", "2", {"broadcaster_user_id": uid, "moderator_user_id": uid}),
        ]
        await asyncio.gather(
            *(
                self.request(
                    "POST",
                    "/eventsub/subscriptions",
                    json={
                        "type": kind,
                        "version": version,
                        "condition": condition,
                        "transport": {"method": "websocket", "session_id": session_id},
                    },
                )
                for kind, version, condition in subscriptions
            )
        )

    async def run_events(
        self,
        on_event: Callable[[dict], Awaitable[None]],
        on_health: Callable[[str, str | None], None],
    ) -> None:
        delay = 1
        while True:
            ws = None
            try:
                if not self.user:
                    on_health("waiting", None)
                    await asyncio.sleep(1)
                    continue
                ws = await websockets.connect(EVENTSUB, ping_interval=None, open_timeout=12)
                self.socket = ws
                welcome = json.loads(await asyncio.wait_for(ws.recv(), 12))
                session = welcome["payload"]["session"]
                await self.subscribe(session["id"])
                timeout = session.get("keepalive_timeout_seconds", 30) + 5
                on_health("connected", None)
                delay = 1
                while True:
                    packet = json.loads(await asyncio.wait_for(ws.recv(), timeout))
                    kind = packet["metadata"]["message_type"]
                    if kind == "notification":
                        await on_event(packet)
                    elif kind == "session_reconnect":
                        # Keep the old connection until the replacement is welcomed.
                        replacement = await websockets.connect(
                            packet["payload"]["session"]["reconnect_url"],
                            ping_interval=None,
                            open_timeout=12,
                        )
                        try:
                            new_welcome = json.loads(await asyncio.wait_for(replacement.recv(), 12))
                            timeout = (
                                new_welcome["payload"]["session"].get(
                                    "keepalive_timeout_seconds", 30
                                )
                                + 5
                            )
                        except BaseException:
                            await replacement.close()
                            raise
                        await ws.close()
                        ws = replacement
                        self.socket = ws
                    elif kind == "revocation":
                        reason = packet["payload"]["subscription"].get("status", "revoked")
                        raise TwitchError(f"EventSub subscription revoked: {reason}")
            except (
                ConnectionClosed,
                OSError,
                TimeoutError,
                ValueError,
                KeyError,
                TwitchError,
                httpx.HTTPError,
            ) as exc:
                error = (
                    str(exc)
                    if isinstance(exc, TwitchError)
                    else "EventSub connection interrupted; reconnecting."
                )
                on_health("reconnecting", error)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 20)
            finally:
                if ws:
                    await ws.close()
                self.socket = None

    async def disconnect(self) -> None:
        if self.device_task:
            self.device_task.cancel()
            await asyncio.gather(self.device_task, return_exceptions=True)
        if self.tokens:
            try:
                await self.http.post(
                    f"{OAUTH}/revoke",
                    data={"client_id": self.client_id, "token": self.tokens["access_token"]},
                )
            except httpx.HTTPError:
                pass
        self.tokens = self.user = self.device = None
        self.credentials.delete("twitch_tokens")
        if self.socket:
            await self.socket.close()

    async def close(self) -> None:
        if self.device_task:
            self.device_task.cancel()
            await asyncio.gather(self.device_task, return_exceptions=True)
        await self.http.aclose()
