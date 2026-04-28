"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ....models.payment_response import PaymentResponse

if TYPE_CHECKING:
    from ..payment_builder import PaymentBuilder


class AuthorizeCaptureCapable:
    """Mixin for payment methods that support authorization (Credit Card)."""

    def authorize(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """Authorize a payment without capturing it (Credit Card only)."""
        return self.execute_action("Authorize", validate=validate)

    def authorizeEncrypted(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """Authorize a payment using encrypted card data (Credit Card only)."""
        return self.execute_action("AuthorizeEncrypted", validate=validate)

    def cancelAuthorize(
        self: 'PaymentBuilder',
        original_transaction_key: Optional[str] = None,
        validate: bool = True,
    ) -> PaymentResponse:
        """Cancel a previously authorized payment.

        Uses AmountCredit (not AmountDebit) per Buckaroo API requirements.
        """
        txn_key = (
            original_transaction_key
            or self._payload.get('original_transaction_key')
            or self._payload.get('authorization_key')
        )
        if not txn_key:
            raise ValueError(
                "original_transaction_key is required for cancelAuthorize"
            )

        request_data = self._build_keyed_request("CancelAuthorize", txn_key, validate=validate)

        if 'AmountDebit' in request_data:
            request_data['AmountCredit'] = request_data.pop('AmountDebit')

        return self._post_transaction(request_data)

    def capture(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """Capture a previously authorized payment."""
        return self.execute_action("Capture", validate=validate)
