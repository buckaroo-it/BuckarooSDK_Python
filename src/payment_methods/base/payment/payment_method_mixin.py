from __future__ import annotations
from typing import Self

from src.transaction import TransactionResponse
from .payment_method_interface import PaymentMethodInterface
from ..has_properties import HasClient, HasPayload


class PaymentMethodMixin(PaymentMethodInterface, HasClient, HasPayload):
    def header(self, data: dict) -> Self:
        return self.client.add_header(data)

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
