from __future__ import annotations

from pydantic import BaseModel, Field


class ChatSnapshot(BaseModel):
    observed_at: float
    users: set[str]
    pages: int = 1


class MetricSample(BaseModel):
    minute: int
    scheduled_at: float
    observed_at: float | None = None
    population: int | None = None
    connected: int | None = None
    spoken: int | None = None
    follows: int | None = None
    error: str | None = None
    chat_complete: bool = True
    cohort_complete: bool = True


class GuestContext(BaseModel):
    name: str = ""
    login: str = ""
    title: str = "Unknown"
    category: str = "Unknown"
    image: str = ""
    clips: list[dict] = Field(default_factory=list)
    error: str | None = None


class RaidRun(BaseModel):
    id: str
    started_at: float
    received_at: float
    source_id: str
    source_login: str
    source_name: str
    viewers: int
    target_id: str = ""
    baseline_at: float | None = None
    baseline_users: set[str] | None = None
    cohort: set[str] = Field(default_factory=set)
    cohort_finalized: bool = False
    cohort_complete: bool = True
    overlap: bool = False
    guest: GuestContext = Field(default_factory=GuestContext)
    learning: dict = Field(default_factory=lambda: {"status": "learning", "messages": 0})
    samples: list[MetricSample] = Field(default_factory=list)
    draft_id: str | None = None

    def public(self) -> dict:
        data = self.model_dump(mode="json", exclude={"baseline_users", "cohort"})
        data["population"] = len(self.cohort) if self.baseline_users is not None else None
        return data


class StreamSummary(BaseModel):
    id: str
    created_at: float
    window_start: float
    window_end: float
    activity: str
    evidence: list[str]


class LandingDraft(BaseModel):
    id: str
    raid_id: str
    text: str
    text_hash: str
    created_at: float
    summary_at: float
    status: str = "pending"
    previewed_at: float | None = None
    message_id: str | None = None
    sent_at: float | None = None
    error: str | None = None
    automatic: bool = False
    template_hash: str = ""
