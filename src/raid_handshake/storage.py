from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import LandingDraft, RaidRun


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        # All operations are serialized by the service event loop. ASGI initialization can
        # happen on a different thread from that loop (e.g. TestClient / embedded launchers).
        self.db = sqlite3.connect(directory / "session.sqlite3", check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS raids (id TEXT PRIMARY KEY, started REAL, data TEXT)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS drafts (id TEXT PRIMARY KEY, created REAL, data TEXT)"
        )

    def save_raid(self, raid: RaidRun) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO raids VALUES (?, ?, ?)",
            (raid.id, raid.started_at, raid.model_dump_json()),
        )
        self.db.commit()

    def save_draft(self, draft: LandingDraft) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO drafts VALUES (?, ?, ?)",
            (draft.id, draft.created_at, draft.model_dump_json()),
        )
        self.db.commit()

    def load(self, now: float) -> tuple[list[RaidRun], list[LandingDraft]]:
        self.prune(now)
        raids = [
            RaidRun.model_validate_json(row[0])
            for row in self.db.execute("SELECT data FROM raids ORDER BY started")
        ]
        drafts = [
            LandingDraft.model_validate_json(row[0])
            for row in self.db.execute("SELECT data FROM drafts ORDER BY created")
        ]
        for draft in drafts:
            if draft.status == "sending":
                draft.status = "uncertain"
                draft.error = "App stopped while sending; check Twitch before sending again."
        return raids, drafts

    def prune(self, now: float) -> None:
        self.db.execute("DELETE FROM raids WHERE started < ?", (now - 3600,))
        self.db.execute("DELETE FROM drafts WHERE created < ?", (now - 3600,))
        self.db.commit()

    def close(self) -> None:
        self.db.close()
