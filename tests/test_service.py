import asyncio
import time
from unittest.mock import AsyncMock

import httpx
import pytest

from raid_handshake.config import Settings
from raid_handshake.models import ChatSnapshot, LandingDraft, RaidRun, StreamSummary
from raid_handshake.service import Service, digest
from raid_handshake.twitch import TwitchError


@pytest.fixture
async def service(tmp_path, credentials):
    instance = Service(Settings(data_dir=tmp_path), credentials)
    instance.twitch.user = {"id": "receiver", "login": "receiver", "display_name": "Receiver"}
    instance._sync_owner()
    yield instance
    await instance.close()


def ready_draft(service, identity="draft", raid_id="raid"):
    text = "We are testing an actual game mechanic. Be kind."
    draft = LandingDraft(
        id=identity,
        raid_id=raid_id,
        text=text,
        text_hash=digest(text),
        created_at=time.time(),
        summary_at=time.time(),
    )
    service.drafts[identity] = draft
    return draft


async def test_default_hotkey_path_requires_a_complete_preview(service):
    draft = ready_draft(service)
    service.twitch.send_chat = AsyncMock(return_value={"message_id": "message"})
    with pytest.raises(ValueError, match="preview"):
        await service.send(draft.id)
    service.twitch.send_chat.assert_not_awaited()
    service.preview(draft.id, draft.text_hash)
    await service.send(draft.id)
    assert draft.status == "sent"


async def test_concurrent_hotkey_and_button_press_send_only_once(service):
    draft = ready_draft(service)
    service.preview(draft.id, draft.text_hash)
    service.twitch.send_chat = AsyncMock(return_value={"message_id": "message"})
    outcomes = await asyncio.gather(
        service.send(draft.id), service.send(draft.id), return_exceptions=True
    )
    assert service.twitch.send_chat.await_count == 1
    assert sum(isinstance(result, ValueError) for result in outcomes) == 1


async def test_ambiguous_network_timeout_is_never_blindly_retried(service):
    draft = ready_draft(service)
    service.preview(draft.id, draft.text_hash)
    service.twitch.send_chat = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))
    await service.send(draft.id)
    assert draft.status == "uncertain"
    with pytest.raises(ValueError):
        await service.send(draft.id)
    assert service.twitch.send_chat.await_count == 1


async def test_known_twitch_rejection_is_reported_as_failed(service):
    draft = ready_draft(service)
    service.preview(draft.id, draft.text_hash)
    service.twitch.send_chat = AsyncMock(side_effect=TwitchError("Not permitted", 403))
    await service.send(draft.id)
    assert draft.status == "failed"


async def test_stale_transcript_cannot_be_sent(service):
    draft = ready_draft(service)
    draft.summary_at = time.time() - 121
    service.preview(draft.id, draft.text_hash)
    service.twitch.send_chat = AsyncMock()
    with pytest.raises(ValueError, match="stale"):
        await service.send(draft.id)
    assert draft.status == "expired"
    service.twitch.send_chat.assert_not_awaited()


async def test_second_draft_cannot_cause_duplicate_message_for_one_raid(service):
    first = ready_draft(service, "first")
    second = ready_draft(service, "second")
    service.preview(first.id, first.text_hash)
    service.preview(second.id, second.text_hash)
    service.twitch.send_chat = AsyncMock(return_value={"message_id": "message"})
    await service.send(first.id)
    with pytest.raises(ValueError, match="Another message"):
        await service.send(second.id)
    assert service.twitch.send_chat.await_count == 1


async def test_approved_template_fills_fresh_summary_and_sends_without_per_card_preview(service):
    now = time.time()
    service.summary = StreamSummary(
        id="summary",
        created_at=now,
        window_start=now - 60,
        window_end=now,
        activity="We are attempting a speedrun.",
        evidence=["attempting a speedrun"],
    )
    event = RaidRun(
        id="raid",
        started_at=now,
        received_at=now,
        source_id="source",
        source_login="source",
        source_name="Source",
        viewers=3,
    )
    service.metrics.begin(event)
    service.update_config({"preapproved_enabled": True}, approve_template=True)
    service.twitch.send_chat = AsyncMock(return_value={"message_id": "message"})
    await service._landing(event)
    draft = service.drafts[event.draft_id]
    assert draft.automatic and draft.status == "sent"
    assert "We are attempting a speedrun." in draft.text
    assert draft.previewed_at is None


async def test_missing_audio_never_generates_a_title_only_landing_card(service):
    now = time.time()
    event = RaidRun(
        id="raid",
        started_at=now,
        received_at=now,
        source_id="source",
        source_login="source",
        source_name="Source",
        viewers=3,
    )
    await service._landing(event)
    assert event.draft_id is None


async def test_duplicate_eventsub_delivery_does_not_create_second_raid(service):
    now = time.time()
    service.metrics.observe(ChatSnapshot(observed_at=now - 1, users={"existing"}))
    service.twitch.guest = AsyncMock(
        return_value=service.metrics.raids[-1].guest if service.metrics.raids else None
    )
    service._guest_context = AsyncMock()
    packet = {
        "metadata": {"message_id": "real-delivery-id"},
        "payload": {
            "subscription": {"type": "channel.raid"},
            "event": {
                "from_broadcaster_user_id": "source",
                "from_broadcaster_user_login": "source",
                "from_broadcaster_user_name": "Source",
                "to_broadcaster_user_id": "receiver",
                "viewers": 8,
            },
        },
    }
    await service.on_event(packet)
    await service.on_event(packet)
    await asyncio.gather(*list(service.tasks))
    assert len(service.metrics.raids) == 1
    assert service.metrics.raids[0].baseline_users == {"existing"}


async def test_preview_hash_must_match_exact_text(service):
    draft = ready_draft(service)
    with pytest.raises(ValueError, match="changed"):
        service.preview(draft.id, "a-different-version")


async def test_app_landing_message_does_not_inflate_participant_speech(service):
    draft = ready_draft(service)
    draft.status = "sent"
    packet = {
        "metadata": {"message_id": "own-chat-message"},
        "payload": {
            "subscription": {"type": "channel.chat.message"},
            "event": {
                "chatter_user_id": "receiver",
                "message_type": "text",
                "message": {
                    "text": draft.text,
                    "fragments": [{"type": "text", "text": draft.text}],
                },
            },
        },
    }
    await service.on_event(packet)
    assert len(service.metrics.messages) == 0


async def test_repeated_text_for_different_raids_requires_a_separate_preview(service):
    first = ready_draft(service, "one", "raid-one")
    second = ready_draft(service, "two", "raid-two")
    service.preview(first.id, first.text_hash)
    assert second.text_hash == first.text_hash
    assert second.previewed_at is None
    service.twitch.send_chat = AsyncMock()
    with pytest.raises(ValueError, match="preview"):
        await service.send(second.id)


async def test_critical_status_is_pushed_without_waiting_for_periodic_timer(service):
    listener = asyncio.Queue(maxsize=1)
    service._subscribers.add(listener)
    service.note("raid", "Real event received")
    assert listener.get_nowait() is True
