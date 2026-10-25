import asyncio
import json
import time
from urllib.parse import parse_qs

import httpx
import pytest

from raid_handshake.twitch import SCOPES, Twitch, TwitchError


@pytest.fixture
async def twitch(credentials):
    client = Twitch("publicclient", credentials)
    client.tokens = {
        "access_token": "fake-access",
        "refresh_token": "fake-refresh",
        "expires_at": time.time() + 3600,
        "client_id": "publicclient",
    }
    client.user = {"id": "receiver", "login": "receiver", "display_name": "Receiver"}
    yield client
    await client.close()


async def transport(client, handler):
    await client.http.aclose()
    client.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_chatter_pagination_is_complete_before_returning_snapshot(twitch):
    def handler(request):
        assert request.url.params["moderator_id"] == "receiver"
        assert request.url.params["first"] == "1000"
        if request.url.params.get("after") == "next":
            return httpx.Response(200, json={"data": [{"user_id": "two"}], "pagination": {}})
        return httpx.Response(
            200, json={"data": [{"user_id": "one"}], "pagination": {"cursor": "next"}}
        )

    await transport(twitch, handler)
    sample = await twitch.chatters()
    assert sample.users == {"one", "two"} and sample.pages == 2


async def test_failed_page_does_not_return_partial_or_empty_chatters(twitch):
    def handler(request):
        if request.url.params.get("after"):
            return httpx.Response(403, json={"message": "no permission"})
        return httpx.Response(
            200, json={"data": [{"user_id": "one"}], "pagination": {"cursor": "next"}}
        )

    await transport(twitch, handler)
    with pytest.raises(TwitchError):
        await twitch.chatters()


async def test_public_refresh_is_serialized_and_rotating_token_is_saved(twitch, credentials):
    refreshes = []

    def handler(request):
        form = parse_qs(request.content.decode())
        assert "client_secret" not in form
        refreshes.append(form["refresh_token"][0])
        return httpx.Response(
            200,
            json={
                "access_token": "replacement",
                "refresh_token": "rotated",
                "expires_in": 3600,
                "scope": list(SCOPES),
            },
        )

    await transport(twitch, handler)
    twitch.tokens["expires_at"] = 0
    result = await asyncio.gather(*(twitch.access_token() for _ in range(4)))
    assert result == ["replacement"] * 4
    assert refreshes == ["fake-refresh"]
    assert json.loads(credentials.get("twitch_tokens"))["refresh_token"] == "rotated"


async def test_device_flow_requests_required_scopes_without_client_secret(twitch):
    def handler(request):
        form = parse_qs(request.content.decode())
        assert set(form["scopes"][0].split()) == set(SCOPES)
        assert "client_secret" not in form
        return httpx.Response(
            200,
            json={
                "device_code": "private-device-code",
                "user_code": "ABCD",
                "verification_uri": "https://www.twitch.tv/activate",
                "expires_in": 600,
                "interval": 5,
            },
        )

    await transport(twitch, handler)
    login = await twitch.begin_device()
    assert login["user_code"] == "ABCD"
    assert "device_code" not in login


async def test_send_chat_uses_connected_broadcaster_as_sender(twitch):
    def handler(request):
        data = json.loads(request.content)
        assert data["sender_id"] == data["broadcaster_id"] == "receiver"
        return httpx.Response(200, json={"data": [{"message_id": "message", "is_sent": True}]})

    await transport(twitch, handler)
    assert (await twitch.send_chat("Real message"))["message_id"] == "message"


async def test_eventsub_subscriptions_have_the_right_versions_and_conditions(twitch):
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(202, json={"data": []})

    await transport(twitch, handler)
    await twitch.subscribe("socket-session")
    by_type = {body["type"]: body for body in bodies}
    assert by_type["channel.raid"]["condition"] == {"to_broadcaster_user_id": "receiver"}
    assert by_type["channel.follow"]["version"] == "2"
    assert by_type["channel.follow"]["condition"]["moderator_user_id"] == "receiver"
    assert all(
        body["transport"] == {"method": "websocket", "session_id": "socket-session"}
        for body in bodies
    )
