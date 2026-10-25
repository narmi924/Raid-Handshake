from __future__ import annotations

import os

import keyring
from keyring.errors import KeyringError


class Credentials:
    """Never falls back to writing credentials to plaintext files."""

    def __init__(self, namespace: str = "Raid Handshake"):
        self.namespace = namespace
        self.memory: dict[str, str] = {}
        self.storage = "OS credential manager"
        self.hidden: set[str] = set()

    def get(self, name: str) -> str | None:
        if name in self.hidden:
            return None
        if name in self.memory:
            return self.memory[name]
        if name == "openai_api_key" and os.getenv("OPENAI_API_KEY"):
            return os.environ["OPENAI_API_KEY"]
        try:
            return keyring.get_password(self.namespace, name)
        except (KeyringError, RuntimeError):
            self.storage = "Session memory (credential manager unavailable)"
            return None

    def set(self, name: str, value: str) -> None:
        self.hidden.discard(name)
        self.memory[name] = value
        try:
            keyring.set_password(self.namespace, name, value)
        except (KeyringError, RuntimeError):
            self.storage = "Session memory (credential manager unavailable)"

    def delete(self, name: str) -> None:
        self.hidden.add(name)
        self.memory.pop(name, None)
        try:
            keyring.delete_password(self.namespace, name)
        except (KeyringError, RuntimeError):
            pass
