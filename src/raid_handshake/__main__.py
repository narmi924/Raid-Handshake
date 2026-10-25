from __future__ import annotations

import uvicorn

from .app import create_app
from .config import Settings


def main() -> None:
    settings = Settings()
    if settings.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("Raid Handshake must bind to localhost.")
    print(f"Raid Handshake control room: http://127.0.0.1:{settings.port}", flush=True)
    print("Real Twitch EventSub only. Account setup: docs/FIRST_REAL_RAID.zh-CN.md", flush=True)
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        access_log=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
