from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAID_", env_file=".env", extra="ignore")
    host: str = "127.0.0.1"
    port: int = 8765
    data_dir: Path = Path("data")
    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    twitch_client_id: str = Field(default="", validation_alias="TWITCH_CLIENT_ID")


class ChannelConfig(BaseModel):
    twitch_client_id: str = Field(default="", max_length=128)
    transcription_model: str = Field(default="gpt-transcribe", min_length=1, max_length=100)
    summary_model: str = Field(default="gpt-4.1-mini", min_length=1, max_length=100)
    commands: str = Field(default="", max_length=100)
    rule: str = Field(default="Be kind and follow the channel rules.", max_length=100)
    template: str = Field(default="Welcome in! {summary} {commands} {rule}", max_length=350)
    language: str = Field(default="English", min_length=1, max_length=40)
    preapproved_enabled: bool = False
    approved_template_hash: str = ""
    chatters_poll_seconds: int = Field(default=5, ge=5, le=30)
    transcript_window_seconds: int = Field(default=180, ge=60, le=600)
    summary_interval_seconds: int = Field(default=30, ge=15, le=120)
    audio_device_id: str = Field(default="", max_length=500)
    global_hotkey: bool = True

    @field_validator("twitch_client_id")
    @classmethod
    def client_id_format(cls, value: str) -> str:
        value = value.strip()
        if value and not value.isalnum():
            raise ValueError("Client ID must contain only letters and numbers.")
        return value

    @field_validator("template")
    @classmethod
    def template_fields(cls, value: str) -> str:
        import string

        fields = list(string.Formatter().parse(value))
        for _, name, format_spec, conversion in fields:
            if name is not None and (
                name not in {"summary", "commands", "rule"} or format_spec or conversion
            ):
                raise ValueError("Only {summary}, {commands}, and {rule} are supported.")
        if not any(name == "summary" for _, name, _, _ in fields):
            raise ValueError("The template must include {summary}.")
        return value

    def template_hash(self) -> str:
        raw = json.dumps([self.template, self.commands, self.rule, self.language])
        return hashlib.sha256(raw.encode()).hexdigest()

    def render(self, summary: str) -> str:
        text = " ".join(
            self.template.format(summary=summary, commands=self.commands, rule=self.rule).split()
        )
        if len(text) > 500:
            raise ValueError("The complete landing card exceeds Twitch's 500-character limit.")
        if not text:
            raise ValueError("The landing card is empty.")
        return text


class ConfigStore:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "config.json"

    def load(self) -> ChannelConfig:
        if not self.path.exists():
            return ChannelConfig()
        return ChannelConfig.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, config: ChannelConfig) -> None:
        temp = self.path.with_suffix(".tmp")
        temp.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        temp.replace(self.path)
