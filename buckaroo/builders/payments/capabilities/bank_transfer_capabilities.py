
"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from typing import TYPE_CHECKING
from ....models.payment_response import PaymentResponse
from .instant_refund_capable import InstantRefundCapable
from .fast_checkout_capable import FastCheckoutCapable

if TYPE_CHECKING:
    from ..payment_builder import PaymentBuilder


class BankTransferCapabilities(InstantRefundCapable, FastCheckoutCapable):
    """Combined capabilities for bank transfer payment methods."""
    pass