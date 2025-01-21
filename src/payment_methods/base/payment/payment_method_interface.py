from __future__ import annotations
from typing import Self, Protocol

from src.transaction import TransactionResponse


class PaymentMethodInterface(Protocol):
    def header(self, data: dict) -> Self:
        return self

    def execute(self) -> TransactionResponse:
        return TransactionResponse(
            {
                "status": 200,
                "message": "OK",
            },
            {
                "currency": "EUR",
                "returnURL": "https://www.example.com/return",
                "returnURLCancel": "https://www.example.com/cancel",
                "pushURL": "https://www.example.com/push",
            },
        )
