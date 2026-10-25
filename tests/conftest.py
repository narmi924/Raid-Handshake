import pytest

from raid_handshake.credentials import Credentials


class MemoryCredentials(Credentials):
    def __init__(self):
        self.memory = {}
        self.storage = "Test memory"

    def get(self, name):
        return self.memory.get(name)

    def set(self, name, value):
        self.memory[name] = value

    def delete(self, name):
        self.memory.pop(name, None)


@pytest.fixture
def credentials():
    return MemoryCredentials()
