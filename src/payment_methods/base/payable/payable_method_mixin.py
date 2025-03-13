from typing import Self
from abc import ABC, abstractmethod

import src.payment_methods.base.payment.payment_method_mixin as payment_method_mixin
import src.models.payload.payload as payload
import src.models.payload.pay_payload as pay_payload
import src.models.payload.refund_payload as refund_payload
import src.transaction.request.transaction_request as transaction_request
import src.models.service_list as service_list
import src.payment_methods.base.payable.payable_method_interface as payable_method_interface


class PayableMethodMixin(
    payment_method_mixin.PaymentMethodMixin,
    payable_method_interface.PayableMethodInterface,
    ABC,
):
    _pay_model: pay_payload.PayPayload
    _refund_model: refund_payload.RefundPayload
    _transaction_request: transaction_request.TransactionRequest = (
        transaction_request.TransactionRequest()
    )

    def pay(self, data: dict) -> Self:
        self._set_pay_payload(data)
        self._set_service_list(self._pay_model, "Pay")

        return self

    def refund(self, data: dict) -> Self:
        self._set_refund_payload(data)
        self._set_service_list(self._refund_model, "Refund")

        return self

    def pay_remainder(self, data: dict) -> Self:
        self._set_pay_remainder_payload(data)
        self._set_service_list(self._pay_model, "PayRemainder")

        return self

    def _set_pay_payload(self, data: dict) -> None:
        self._pay_model = pay_payload.PayPayload(data)

        self._transaction_request.set_payload(self._pay_model)

    def _set_refund_payload(self, data: dict) -> None:
        self._refund_model = refund_payload.RefundPayload(data)

        self._transaction_request.set_payload(self._refund_model)

    def _set_pay_remainder_payload(self, data: dict) -> None:
        self._pay_model = pay_payload.PayPayload(data)
        self._transaction_request.set_payload(self._pay_model)

    def _set_service_list(self, payload: payload.Payload, action: str) -> None:
        new_service_list = service_list.ServiceList(
            self.payment_name, self.service_version, action, payload
        )
        self._transaction_request.set_services(new_service_list)

    @property
    @abstractmethod
    def payment_name(self) -> str:
        pass

    @property
    @abstractmethod
    def service_version(self) -> int:
        pass
