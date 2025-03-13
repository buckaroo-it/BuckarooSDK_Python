from __future__ import annotations

import src.transaction.client as client
import src.transaction.request.transaction_request as transaction_request
import src.payment_methods.base.payable.payable_method_mixin as payable_method_mixin


class Ideal(payable_method_mixin.PayableMethodMixin):
    def __init__(self, client: client.Client):
        self._client = client
        self._transaction_request = transaction_request.TransactionRequest()

    @property
    def client(self) -> client.Client:
        return self._client

    @property
    def transaction_request(self) -> transaction_request.TransactionRequest:
        return self._transaction_request

    @property
    def payment_name(self) -> str:
        return "ideal"

    @property
    def service_version(self) -> int:
        return 0
