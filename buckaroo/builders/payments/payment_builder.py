from __future__ import annotations

from typing import Dict, Any, Optional

from ..base_builder import BaseBuilder
from ...models.payment_response import PaymentResponse


class PaymentBuilder(BaseBuilder):
    """Base class for all payment method builders.

    Adds payment lifecycle methods (pay, refund, capture, cancel, execute_action)
    that are specific to payment flows.  ``SolutionBuilder`` inherits from
    ``BaseBuilder`` directly and does NOT get these methods.
    """

    def pay(self, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        """Execute the payment."""
        request_data = self.build("Pay", validate=validate, strict_validation=strict_validation).to_dict()
        return self._post_transaction(request_data)

    def refund(
        self,
        original_transaction_key: Optional[str] = None,
        amount: Optional[float] = None,
        validate: bool = True,
    ) -> PaymentResponse:
        """Execute a full refund."""
        txn_key = original_transaction_key or self._payload.get('original_transaction_key')
        if not txn_key:
            raise ValueError("Original transaction key is required for refund")

        refund_amount = amount if amount is not None else self._payload.get('refund_amount')
        request_data = self._build_keyed_request('Refund', txn_key, validate=validate)

        if refund_amount is not None:
            request_data['AmountCredit'] = refund_amount
            request_data.pop('AmountDebit', None)
        else:
            if 'AmountDebit' in request_data:
                request_data['AmountCredit'] = request_data.pop('AmountDebit')

        return self._post_transaction(request_data)

    def partial_refund(
        self,
        original_transaction_key: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> PaymentResponse:
        """Execute a partial refund."""
        if not amount or amount <= 0:
            raise ValueError("Partial refund amount must be greater than 0")

        _MISSING = object()
        saved_key = self._payload.get('original_transaction_key', _MISSING)
        saved_amount = self._payload.get('refund_amount', _MISSING)

        if original_transaction_key is not None:
            self._payload['original_transaction_key'] = original_transaction_key
        self._payload['refund_amount'] = amount

        try:
            return self.refund()
        finally:
            if saved_key is _MISSING:
                self._payload.pop('original_transaction_key', None)
            else:
                self._payload['original_transaction_key'] = saved_key
            if saved_amount is _MISSING:
                self._payload.pop('refund_amount', None)
            else:
                self._payload['refund_amount'] = saved_amount

    def capture(
        self,
        original_transaction_key: Optional[str] = None,
        amount: Optional[float] = None,
        validate: bool = True,
    ) -> PaymentResponse:
        """Capture a previously authorized payment."""
        auth_key = (
            original_transaction_key
            or self._payload.get('authorization_key')
            or self._payload.get('original_transaction_key')
        )
        if not auth_key:
            raise ValueError("Authorization key is required for capture")

        capture_amount = amount if amount is not None else self._payload.get('capture_amount')
        request_data = self._build_keyed_request('Capture', auth_key, validate=validate)

        if capture_amount is not None:
            request_data['AmountDebit'] = capture_amount

        return self._post_transaction(request_data)

    def cancel(self, original_transaction_key: Optional[str] = None) -> PaymentResponse:
        """Cancel a pending or authorized transaction."""
        txn_key = (
            original_transaction_key
            or self._payload.get('cancel_key')
            or self._payload.get('original_transaction_key')
        )
        if not txn_key:
            raise ValueError("Transaction key is required for cancel")

        request_data = self._build_keyed_request('Pay', txn_key)
        request_data.pop('AmountDebit', None)
        request_data.pop('AmountCredit', None)

        return self._post_transaction(request_data)

    def execute_action(self, action: str, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        """Execute any named action supported by this payment method."""
        request_data = self.build(action, validate=validate, strict_validation=strict_validation).to_dict()
        return self._post_transaction(request_data)

    def _build_keyed_request(self, action: str, txn_key: str, validate: bool = True) -> Dict[str, Any]:
        """Build a request dict that references an original transaction."""
        request_data = self.build(action, validate=validate).to_dict()
        request_data['OriginalTransactionKey'] = txn_key
        return request_data
