from __future__ import annotations
from typing import Self

import src.transaction.response.transaction_response as transaction_response
import src.payment_methods.base.payment.payment_method_interface as payment_method_interface
import src.payment_methods.base.has_properties as has_properties


class PaymentMethodMixin(
    payment_method_interface.PaymentMethodInterface,
    has_properties.HasClient,
    has_properties.HasTransationRequest,
):
    def header(self, data: dict) -> Self:
        self.client.add_header(data)
        return self

    def execute(self) -> transaction_response.TransactionResponse:
        return self.client.post(self.transaction_request)
