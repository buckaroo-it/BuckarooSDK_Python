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


class InstantRefundCapable:
    """Mixin for payment methods that support instant refunds (iDEAL, Sofort, PayConiq)."""

    def instant_refund(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """Initiate an instant refund (iDEAL, Sofort, PayConiq only)."""
        return self.execute_action("instantRefund", validate=validate)
