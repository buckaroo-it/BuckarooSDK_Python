from typing import Self

from .payable_method_interface import PayableMethodInterface
from ..payment.payment_method_mixin import PaymentMethodMixin
from ..has_properties import HasClient
from src.models import PayPayload, RefundPayload, ModelInterface
from src.transaction import TransactionRequest

class PayableMethodMixin(PayableMethodInterface, PaymentMethodMixin):
    _pay_model: PayPayload
    _refund_model: RefundPayload
    _transaction_request: TransactionRequest

    def pay(self, data: dict) -> Self:
        self._set_pay_payload()

        return self

    def refund(self, data: dict) -> Self:
        return self

    def pay_remainder(self, data: dict) -> Self:
        return self
    
    def _set_pay_payload(self) -> None:
        self._pay_model = PayPayload(self.payload)
        self._transaction_request = TransactionRequest(self._pay_model)
        
        self._transaction_request.set_payload(self._pay_model)

    # def _set_service_list(action: str?, model: ModelInterface = None) -> Self




