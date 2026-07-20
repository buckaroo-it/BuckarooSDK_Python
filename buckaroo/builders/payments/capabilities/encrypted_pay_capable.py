"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ....models.payment_response import PaymentResponse

if TYPE_CHECKING:
    from ..payment_builder import PaymentBuilder


class EncryptedPayCapable:
    """Mixin for payment methods that support encryption (Credit Card)."""

    def payEncrypted(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """Process a payment using encrypted card data (Credit Card only)."""
        return self.execute_action("PayEncrypted", validate=validate)
