import pytest
from fastapi.testclient import TestClient

from raid_handshake.app import create_app
from raid_handshake.config import Settings


@pytest.fixture
def client(tmp_path, credentials):
    app = create_app(Settings(data_dir=tmp_path), credentials, background=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as http:
        yield http


def headers(client):
    return {"X-CSRF-Token": client.get("/api/session").json()["csrf_token"]}


def test_mutations_require_local_session_token(client):
    assert client.post("/api/config", json={"values": {"rule": "A rule"}}).status_code == 403
    assert (
        client.post(
            "/api/config", json={"values": {"rule": "A rule"}}, headers=headers(client)
        ).status_code
        == 200
    )


def test_host_and_origin_are_checked(client):
    assert client.get("/api/state", headers={"Host": "attacker.example"}).status_code == 403
    auth = dict(headers(client), Origin="https://attacker.example")
    assert client.post("/api/audio/stop", headers=auth).status_code == 403


def test_saved_api_key_never_appears_in_responses_or_state(client):
    secret = "test-only-api-key-do-not-use"
    response = client.post("/api/openai/key", json={"api_key": secret}, headers=headers(client))
    assert response.status_code == 200
    assert secret not in response.text
    assert secret not in client.get("/api/state").text
    assert client.get("/api/state").json()["health"]["openai_configured"]


def test_invalid_secret_is_not_echoed_in_validation_error(client):
    response = client.post("/api/openai/key", json={"api_key": "secret"}, headers=headers(client))
    assert response.status_code == 422
    assert "secret" not in response.text


def test_automatic_mode_is_off_until_explicit_template_approval(client):
    state = client.get("/api/state").json()
    assert state["config"]["preapproved_enabled"] is False
    assert (
        client.post(
            "/api/config", json={"values": {"preapproved_enabled": True}}, headers=headers(client)
        ).status_code
        == 400
    )
    response = client.post(
        "/api/template/approval",
        json={"enabled": True, "template_hash": state["template_hash"]},
        headers=headers(client),
    )
    assert response.json()["enabled"] is True
    client.post("/api/config", json={"values": {"rule": "A changed rule"}}, headers=headers(client))
    assert not client.get("/api/state").json()["config"]["preapproved_enabled"]


def test_invalid_template_fields_are_rejected(client):
    response = client.post(
        "/api/config", json={"values": {"template": "{summary.__class__}"}}, headers=headers(client)
    )
    assert response.status_code == 400


def test_no_simulated_raid_route_is_exposed(client):
    assert client.post("/api/raids/simulate", headers=headers(client)).status_code == 404
    assert client.get("/api/health").json()["events"] == "real Twitch EventSub only"


def test_context_never_uses_title_only_fallback(client):
    response = client.post("/api/summary/refresh", headers=headers(client))
    assert response.status_code == 409


def test_overlay_websocket_cannot_read_admin_secrets(client):
    url = client.get("/api/session").json()["overlay_url"]
    token = url.split("key=", 1)[1]
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"view": "overlay", "token": token})
        data = ws.receive_json()
        assert "config" not in data and "transcript" not in data and "device_login" not in data


def test_old_template_revision_cannot_be_approved(client):
    state = client.get("/api/state").json()
    client.post("/api/config", json={"values": {"rule": "new"}}, headers=headers(client))
    response = client.post(
        "/api/template/approval",
        json={"enabled": True, "template_hash": state["template_hash"]},
        headers=headers(client),
    )
    assert response.status_code == 409
