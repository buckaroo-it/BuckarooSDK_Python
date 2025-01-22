from __future__ import annotations

from src.transaction import Client
from ..base.payable.payable_method_mixin import PayableMethodMixin
from ..base.payment.payment_method_mixin import PaymentMethodMixin


class Ideal(PayableMethodMixin, PaymentMethodMixin):
    def __init__(self, client: Client):
        self._payment_name = "ideal"
        self._required_config_fields = [
            "currency",
            "returnURL",
            "returnURLCancel",
            "pushURL",
        ]
        self._client = client

    @property
    def client(self) -> Client:
        return self._client
