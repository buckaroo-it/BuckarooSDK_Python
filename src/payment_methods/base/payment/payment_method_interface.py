from __future__ import annotations
from typing import Self
from abc import ABC, abstractmethod

from src.transaction import TransactionResponse


class PaymentMethodInterface(ABC):
    @abstractmethod
    def header(self, data: dict) -> Self:
        pass

    @abstractmethod
    def execute(self) -> TransactionResponse:
        pass
