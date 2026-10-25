from raid_handshake.metrics import Metrics
from raid_handshake.models import ChatSnapshot, RaidRun


def raid(start=100, identity="raid-1"):
    return RaidRun(
        id=identity,
        started_at=start,
        received_at=start,
        source_id="source",
        source_login="source",
        source_name="Source",
        viewers=20,
    )


def snapshot(when, *users):
    return ChatSnapshot(observed_at=when, users=set(users))


def test_union_arrivals_not_in_baseline_and_late_arrivals_excluded():
    engine = Metrics()
    engine.observe(snapshot(98, "existing"))
    event = raid()
    engine.begin(event)
    engine.observe(snapshot(105, "existing", "alice"))
    engine.observe(snapshot(110, "existing", "bob"))
    engine.observe(snapshot(191, "existing", "too-late"))
    assert event.cohort == {"alice", "bob"}
    assert event.cohort_finalized
    engine.add_message(390, "alice")
    engine.add_message(391, "outsider")
    engine.add_follow(115, "follow-1")
    engine.add_follow(401, "not-yet")
    engine.observe(snapshot(400, "existing", "bob", "too-late"))
    sample = event.samples[0]
    assert (sample.population, sample.connected, sample.spoken, sample.follows) == (2, 1, 1, 1)


def test_spoken_is_a_trailing_five_minute_window_not_cumulative():
    engine = Metrics()
    engine.observe(snapshot(99))
    event = raid()
    engine.begin(event)
    engine.observe(snapshot(102, "early", "recent"))
    engine.add_message(110, "early")
    engine.add_message(990, "recent")
    engine.add_message(995, "not-ordinary", ordinary=False)
    engine.observe(snapshot(1000, "early", "recent"))
    sample = next(item for item in event.samples if item.minute == 15)
    assert sample.spoken == 1


def test_missing_baseline_is_unknown_not_an_empty_baseline():
    engine = Metrics()
    event = raid()
    engine.begin(event)
    engine.observe(snapshot(105, "everyone"))
    engine.observe(snapshot(400, "everyone"))
    assert event.public()["population"] is None
    assert event.samples[0].connected is None
    assert event.samples[0].error == "No complete pre-raid baseline"


def test_a_real_empty_baseline_is_valid():
    engine = Metrics()
    engine.observe(snapshot(99))
    event = raid()
    engine.begin(event)
    engine.observe(snapshot(105, "new"))
    assert event.cohort == {"new"}
    assert event.baseline_users == set()


def test_stale_baseline_is_not_used():
    engine = Metrics()
    engine.observe(snapshot(80, "old"))
    event = raid()
    engine.begin(event)
    assert event.baseline_users is None


def test_delayed_eventsub_notification_uses_pre_event_snapshot_and_recent_history():
    engine = Metrics()
    engine.observe(snapshot(99, "old"))
    engine.observe(snapshot(104, "old", "arrived"))
    event = raid()
    event.received_at = 106
    engine.begin(event)
    assert event.baseline_users == {"old"}
    assert event.cohort == {"arrived"}


def test_overlapping_raids_are_flagged_instead_of_claiming_clean_attribution():
    engine = Metrics()
    engine.observe(snapshot(99, "old"))
    first = raid()
    second = raid(130, "raid-2")
    engine.begin(first)
    engine.begin(second)
    assert first.overlap and second.overlap


def test_missed_checkpoint_never_uses_a_later_snapshot_as_if_it_were_on_time():
    engine = Metrics()
    engine.observe(snapshot(99))
    event = raid()
    engine.begin(event)
    engine.observe(snapshot(105, "new"))
    engine.observe(snapshot(500, "new"))
    sample = event.samples[0]
    assert sample.connected is None
    assert sample.observed_at is None
    assert sample.error == "Scheduled observation missed"


def test_eventsub_gap_invalidates_messages_and_follows_but_not_chatters():
    engine = Metrics()
    engine.observe(snapshot(99))
    event = raid()
    engine.begin(event)
    engine.observe(snapshot(105, "new"))
    engine.gap(200, 250)
    engine.observe(snapshot(400, "new"))
    sample = event.samples[0]
    assert sample.connected == 1
    assert sample.spoken is None and sample.follows is None
    assert not sample.chat_complete


def test_failed_arrival_poll_is_visible_as_incomplete():
    engine = Metrics()
    engine.observe(snapshot(99))
    event = raid()
    engine.begin(event)
    engine.failed_poll(150)
    assert not event.cohort_complete


def test_public_state_does_not_expose_chatter_ids_or_baseline_lists():
    event = raid()
    event.baseline_users = {"private-baseline-id"}
    event.cohort = {"private-cohort-id"}
    public = event.public()
    assert "baseline_users" not in public and "cohort" not in public
    assert "private-" not in str(public)
