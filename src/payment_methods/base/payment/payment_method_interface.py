from __future__ import annotations
from typing import Self
from abc import ABC, abstractmethod

import src.transaction.response.transaction_response as transaction_response


class PaymentMethodInterface(ABC):
    @abstractmethod
    def header(self, data: dict) -> Self:
        pass

    @abstractmethod
    def execute(self) -> transaction_response.TransactionResponse:
        pass
