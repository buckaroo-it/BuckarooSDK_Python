from abc import ABC, abstractmethod
from __future__ import annotations
from typing import Self

from src.transaction import TransactionResponse


class PaymentMethodBuilderInterface(ABC):

    @abstractmethod
    def header(self, data: dict) -> Self:
        pass

    @abstractmethod
    def execute(self) -> TransactionResponse:
        pass
