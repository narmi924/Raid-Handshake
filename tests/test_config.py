from raid_handshake.config import Settings


def test_dotenv_loads_api_configuration_without_exposing_secret_in_repr(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "OPENAI_API_KEY=sk-fake-test-only\nTWITCH_CLIENT_ID=publicclient\n", encoding="utf-8"
    )
    settings = Settings(_env_file=path)
    assert settings.openai_api_key.get_secret_value() == "sk-fake-test-only"
    assert settings.twitch_client_id == "publicclient"
    assert "sk-fake-test-only" not in repr(settings)
