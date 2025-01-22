from typing import Protocol

from src.transaction import Client


class HasClient(Protocol):
    @property
    def client(self) -> Client: ...
