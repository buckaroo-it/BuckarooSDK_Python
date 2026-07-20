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
    """Mixin contributing the Authorize / CancelAuthorize action surface.

    ``capture`` lives on :class:`BaseBuilder` with the full
    ``original_transaction_key`` / ``amount`` signature and is shared by every
    builder; it is intentionally not duplicated here.
    """

    def authorize(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        """Authorize a payment without capturing it.

        Args:
            validate: Whether to validate service parameters before building.

        Returns:
            PaymentResponse: The authorization response.
        """
        payment_request = self.build("Authorize", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)

    def authorizeEncrypted(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        """Authorize an encrypted-card payment without capturing it.

        Args:
            validate: Whether to validate service parameters before building.

        Returns:
            PaymentResponse: The authorization response.
        """
        payment_request = self.build("AuthorizeEncrypted", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)

    def cancelAuthorize(
        self: "PaymentBuilder",
        original_transaction_key: Optional[str] = None,
        validate: bool = True,
    ) -> PaymentResponse:
        """Cancel a previously authorized payment.

        Uses AmountCredit (not AmountDebit) per Buckaroo API requirements.
        """
        txn_key = (
            original_transaction_key
            or self._payload.get("original_transaction_key")
            or self._payload.get("authorization_key")
        )
        if not txn_key:
            raise ValueError("original_transaction_key is required for cancelAuthorize")

        request_data = self._build_keyed_request("CancelAuthorize", txn_key, validate=validate)

        if "AmountDebit" in request_data:
            request_data["AmountCredit"] = request_data.pop("AmountDebit")

        return self._post_transaction(request_data)
