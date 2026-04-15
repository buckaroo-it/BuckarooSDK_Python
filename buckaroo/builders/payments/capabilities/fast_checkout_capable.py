from __future__ import annotations

"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from typing import TYPE_CHECKING
from ....models.payment_response import PaymentResponse

if TYPE_CHECKING:
    from ..payment_builder import PaymentBuilder


class FastCheckoutCapable:
    """Mixin for payment methods that support fast checkout (iDEAL, Sofort, PayConiq)."""

    def pay_fast_checkout(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """Enable PayFast Checkout (iDEAL, Sofort, PayConiq only)."""
        return self.execute_action("payFastCheckout", validate=validate)

