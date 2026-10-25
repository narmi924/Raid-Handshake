from __future__ import annotations

import asyncio
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from .audio import devices
from .config import ChannelConfig, Settings
from .credentials import Credentials
from .service import Service
from .twitch import TwitchError

STATIC = Path(__file__).parent / "static"


class KeyInput(BaseModel):
    api_key: str = Field(min_length=10, max_length=2000)


class ConfigurationInput(BaseModel):
    values: dict


class PreviewInput(BaseModel):
    text_hash: str


class ApprovalInput(BaseModel):
    enabled: bool
    template_hash: str


def create_app(
    settings: Settings | None = None,
    credentials: Credentials | None = None,
    background: bool = True,
) -> FastAPI:
    settings = settings or Settings()
    service = Service(settings, credentials)
    package_path = Path(__file__).resolve().parent
    guide_path = package_path / "guides" / "FIRST_REAL_RAID.zh-CN.md"
    if not guide_path.is_file():
        guide_path = package_path.parents[1] / "docs" / "FIRST_REAL_RAID.zh-CN.md"

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if background:
            await service.start()
        yield
        await service.close()

    app = FastAPI(
        title="Raid Handshake", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None
    )
    app.state.service = service

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        if request.url.hostname not in {"127.0.0.1", "localhost", "[::1]", "::1"}:
            return JSONResponse(
                {"detail": "This application accepts localhost requests only."}, 403
            )
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            expected = service.admin_token
            supplied = request.headers.get("x-csrf-token", "")
            if not supplied or not secrets.compare_digest(expected, supplied):
                return JSONResponse(
                    {"detail": "Reload the local control room before continuing."}, 403
                )
            origin = request.headers.get("origin")
            allowed = {
                f"http://{host}:{port}"
                for host in ("127.0.0.1", "localhost")
                for port in (settings.port, 5173)
            }
            if origin and origin not in allowed:
                return JSONResponse(
                    {"detail": "Cross-origin control requests are not permitted."}, 403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(TwitchError)
    async def twitch_error(_: Request, exc: TwitchError):
        return JSONResponse({"detail": str(exc)}, 400)

    @app.exception_handler(ValueError)
    async def value_error(_: Request, exc: ValueError):
        return JSONResponse({"detail": str(exc)[:250]}, 400)

    @app.exception_handler(httpx.HTTPError)
    async def network_error(_: Request, __: httpx.HTTPError):
        return JSONResponse({"detail": "Network request failed. Check connection health."}, 502)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, __: RequestValidationError):
        # Default validation errors can echo an invalid API key from the request body.
        return JSONResponse({"detail": "Invalid request fields. Check the input format."}, 422)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0", "events": "real Twitch EventSub only"}

    @app.get("/api/session")
    async def session():
        return {
            "csrf_token": service.admin_token,
            "overlay_url": f"http://127.0.0.1:{settings.port}/overlay?key={service.overlay_token}",
        }

    @app.get("/api/state")
    async def state():
        return service.state()

    @app.post("/api/config")
    async def config(body: ConfigurationInput):
        allowed = set(ChannelConfig.model_fields) - {
            "approved_template_hash",
            "preapproved_enabled",
        }
        if set(body.values) - allowed:
            raise HTTPException(400, "Unsupported configuration fields.")
        try:
            service.update_config(body.values)
        except ValidationError as exc:
            raise HTTPException(400, "; ".join(error["msg"] for error in exc.errors())) from None
        return {"ok": True}

    @app.post("/api/twitch/connect")
    async def connect():
        if service.twitch.user:
            raise HTTPException(
                409, "Disconnect the current Twitch account before connecting another."
            )
        return await service.twitch.begin_device()

    @app.post("/api/twitch/disconnect")
    async def disconnect():
        await service.stop_audio()
        await service.twitch.disconnect()
        service.on_health("waiting", None)
        service.chatters_status = "waiting"
        service.metrics.snapshots.clear()
        return {"ok": True}

    @app.post("/api/openai/key")
    async def save_key(body: KeyInput):
        service.credentials.set("openai_api_key", body.api_key.strip())
        service._dirty = True
        return {"configured": True, "storage": service.credentials.storage}

    @app.delete("/api/openai/key")
    async def delete_key():
        await service.stop_audio()
        service.credentials.delete("openai_api_key")
        service.summary = None
        return {"configured": False}

    @app.get("/api/audio/devices")
    async def audio_devices():
        try:
            return {"devices": await asyncio.to_thread(devices), "error": None}
        except Exception:
            return {
                "devices": [],
                "error": "Audio device enumeration failed. Check Windows permissions.",
            }

    @app.post("/api/audio/start")
    async def audio_start():
        await service.start_audio()
        return {"ok": True}

    @app.post("/api/audio/stop")
    async def audio_stop():
        await service.stop_audio()
        return {"ok": True}

    @app.post("/api/summary/refresh")
    async def summary_refresh():
        summary = await service.refresh_summary(force=True)
        if summary is None:
            raise HTTPException(409, service.summary_error or "A fresh transcript is required.")
        return summary

    @app.post("/api/template/approval")
    async def template_approval(body: ApprovalInput):
        if body.template_hash != service.config.template_hash():
            raise HTTPException(
                409, "The template changed. Review and save the current template first."
            )
        service.update_config({"preapproved_enabled": body.enabled}, approve_template=body.enabled)
        return {"enabled": service.config.preapproved_enabled}

    @app.post("/api/raids/{raid_id}/draft")
    async def rebuild_draft(raid_id: str):
        await service.rebuild_landing(raid_id)
        raid = next(raid for raid in service.metrics.raids if raid.id == raid_id)
        if not raid.draft_id:
            raise HTTPException(409, "Start audio capture and wait for a fresh summary first.")
        return {"ok": True}

    @app.post("/api/drafts/{draft_id}/preview")
    async def preview(draft_id: str, body: PreviewInput):
        if draft_id not in service.drafts:
            raise HTTPException(404, "Landing card not found.")
        service.preview(draft_id, body.text_hash)
        return {"ok": True}

    @app.post("/api/drafts/{draft_id}/send")
    async def send(draft_id: str):
        if draft_id not in service.drafts:
            raise HTTPException(404, "Landing card not found.")
        result = await service.send(draft_id)
        return result

    @app.websocket("/ws")
    async def updates(socket: WebSocket):
        origin = socket.headers.get("origin", "")
        if origin and not any(
            origin == f"http://{host}:{port}"
            for host in ("127.0.0.1", "localhost")
            for port in (settings.port, 5173)
        ):
            await socket.close(code=1008)
            return
        await socket.accept()
        queue: asyncio.Queue = asyncio.Queue(maxsize=1)
        try:
            auth = await asyncio.wait_for(socket.receive_json(), 5)
            token = str(auth.get("token", ""))
            overlay = auth.get("view") == "overlay"
            expected = service.overlay_token if overlay else service.admin_token
            if not token or not secrets.compare_digest(token, expected):
                await socket.close(code=1008)
                return
            service._subscribers.add(queue)
            await socket.send_json(service.state(overlay=overlay))
            while True:
                try:
                    await asyncio.wait_for(queue.get(), 10)
                except TimeoutError:
                    pass
                await socket.send_json(service.state(overlay=overlay))
        except (WebSocketDisconnect, TimeoutError, RuntimeError, ValueError):
            pass
        finally:
            service._subscribers.discard(queue)

    @app.get("/guide")
    async def guide():
        if guide_path.is_file():
            return FileResponse(guide_path, media_type="text/plain; charset=utf-8")
        raise HTTPException(404, "See docs/FIRST_REAL_RAID.zh-CN.md in the source repository.")

    if (STATIC / "assets").exists():
        app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/")
    @app.get("/overlay")
    async def index():
        if (STATIC / "index.html").exists():
            return FileResponse(STATIC / "index.html")
        return JSONResponse(
            {"detail": "Build the interface first: npm install; npm run build"}, 503
        )

    return app
