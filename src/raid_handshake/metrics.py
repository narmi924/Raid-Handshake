from __future__ import annotations

from collections import deque

from .models import ChatSnapshot, MetricSample, RaidRun


class Metrics:
    """Chat-connection estimates. No claim about verified raiders or video viewers."""

    def __init__(self, poll_seconds: int = 5):
        self.poll_seconds = poll_seconds
        self.snapshots: deque[ChatSnapshot] = deque(maxlen=240)
        self.raids: list[RaidRun] = []
        self.messages: deque[tuple[float, str]] = deque()
        self.follows: deque[tuple[float, str]] = deque()
        self.event_gaps: list[tuple[float, float]] = []

    @property
    def latest(self) -> ChatSnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def begin(self, raid: RaidRun) -> None:
        baseline = next(
            (s for s in reversed(self.snapshots) if s.observed_at <= raid.started_at), None
        )
        if baseline and raid.started_at - baseline.observed_at <= self.poll_seconds * 3:
            raid.baseline_at = baseline.observed_at
            raid.baseline_users = set(baseline.users)
        else:
            raid.cohort_complete = False
        for previous in self.raids:
            if 0 <= raid.started_at - previous.started_at < 90:
                previous.overlap = raid.overlap = True
        self.raids.append(raid)
        # An EventSub notification can arrive after a poll; include in-window history.
        for snapshot in self.snapshots:
            self._extend(raid, snapshot)

    def _extend(self, raid: RaidRun, snapshot: ChatSnapshot) -> None:
        if raid.baseline_users is not None and (
            not raid.cohort_finalized
            and raid.started_at <= snapshot.observed_at <= raid.started_at + 90
        ):
            raid.cohort.update(snapshot.users - raid.baseline_users)

    def observe(self, snapshot: ChatSnapshot) -> None:
        previous = self.latest
        self.snapshots.append(snapshot)
        for raid in self.raids:
            if previous and snapshot.observed_at - previous.observed_at > self.poll_seconds * 3:
                if previous.observed_at <= raid.started_at + 90 <= snapshot.observed_at or (
                    raid.started_at <= snapshot.observed_at <= raid.started_at + 90
                ):
                    raid.cohort_complete = False
            self._extend(raid, snapshot)
        self.advance(snapshot.observed_at)

    def failed_poll(self, now: float) -> None:
        for raid in self.raids:
            if raid.started_at <= now <= raid.started_at + 90:
                raid.cohort_complete = False

    def add_message(self, when: float, user_id: str, ordinary: bool = True) -> None:
        if ordinary:
            self.messages.append((when, user_id))

    def add_follow(self, when: float, event_id: str) -> None:
        self.follows.append((when, event_id))

    def gap(self, start: float, end: float) -> None:
        self.event_gaps.append((start, end))

    def _complete(self, start: float, end: float) -> bool:
        return not any(a < end and b > start for a, b in self.event_gaps)

    def advance(self, now: float) -> bool:
        changed = False
        snapshot = self.latest
        for raid in self.raids:
            if now >= raid.started_at + 90 and not raid.cohort_finalized:
                raid.cohort_finalized = True
                changed = True
            for minute in (5, 15, 30):
                due = raid.started_at + minute * 60
                if now < due or any(s.minute == minute for s in raid.samples):
                    continue
                usable = snapshot is not None and due <= snapshot.observed_at <= due + 30
                if not usable and now < due + 30:
                    continue
                observed = snapshot.observed_at if usable and snapshot else None
                end = observed if observed is not None else due
                chat_complete = self._complete(end - 300, end)
                follow_complete = self._complete(raid.started_at, end)
                known = raid.baseline_users is not None
                raid.samples.append(
                    MetricSample(
                        minute=minute,
                        scheduled_at=due,
                        observed_at=observed,
                        population=len(raid.cohort) if known else None,
                        connected=len(raid.cohort & snapshot.users)
                        if usable and snapshot and known
                        else None,
                        spoken=len(
                            {u for t, u in self.messages if end - 300 < t <= end} & raid.cohort
                        )
                        if known and observed is not None and chat_complete
                        else None,
                        follows=len({eid for t, eid in self.follows if raid.started_at <= t <= end})
                        if observed is not None and follow_complete
                        else None,
                        error=(
                            "No complete pre-raid baseline"
                            if not known
                            else "Scheduled observation missed"
                            if not usable
                            else None
                        ),
                        chat_complete=chat_complete,
                        cohort_complete=raid.cohort_complete,
                    )
                )
                changed = True
        # Bounded context, not a historical analytics database.
        cutoff = now - 3600
        self.messages = deque((t, u) for t, u in self.messages if t >= cutoff)
        self.follows = deque((t, e) for t, e in self.follows if t >= cutoff)
        self.event_gaps = [(a, b) for a, b in self.event_gaps if b >= cutoff]
        self.raids = [raid for raid in self.raids if raid.started_at >= cutoff]
        return changed
