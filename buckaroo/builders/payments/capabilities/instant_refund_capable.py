"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ....models.payment_response import PaymentResponse

if TYPE_CHECKING:
    from ..payment_builder import PaymentBuilder


class InstantRefundCapable:
    """Mixin for payment methods that support instant refunds (iDEAL, Sofort, PayConiq)."""

    def instantRefund(
        self: "PaymentBuilder",
        original_transaction_key: Optional[str] = None,
        validate: bool = True,
    ) -> PaymentResponse:
        """
        Initiate an instant refund.

        Mirrors :meth:`BaseBuilder.refund`: puts ``OriginalTransactionKey`` and
        ``AmountCredit`` on the wire instead of ``AmountDebit``, but keeps the
        ``instantRefund`` action name.

        Available for: iDEAL, Sofort, PayConiq
        Not available for: Credit Card, PayPal (use regular refund instead)

        Args:
            original_transaction_key (str, optional): The transaction key of the
                original payment. If None, will try to get from payload.
            validate (bool): Whether to validate service parameters before building

        Returns:
            PaymentResponse: The instant refund response

        Raises:
            ValueError: If no original transaction key is available
        """
        txn_key = original_transaction_key or self._payload.get("original_transaction_key")
        if not txn_key:
            raise ValueError(
                "Original transaction key is required for instant refunds "
                "(provide as parameter or in payload)"
            )

        _MISSING = object()
        prev_key = self._payload.get("original_transaction_key", _MISSING)
        self._payload["original_transaction_key"] = txn_key
        try:
            request_data = self._build_refund_request_data("instantRefund", validate)
        finally:
            if prev_key is _MISSING:
                self._payload.pop("original_transaction_key", None)
            else:
                self._payload["original_transaction_key"] = prev_key

        return self._post_transaction(request_data)
