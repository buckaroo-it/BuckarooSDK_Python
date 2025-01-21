from typing import Protocol, Self

from src.transaction import Client

class HasClient(Protocol):
    @property
    def client(self) -> Client: ...