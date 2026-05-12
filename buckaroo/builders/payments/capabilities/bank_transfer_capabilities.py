"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from __future__ import annotations

from .fast_checkout_capable import FastCheckoutCapable
from .instant_refund_capable import InstantRefundCapable


class BankTransferCapabilities(InstantRefundCapable, FastCheckoutCapable):
    """Combined capabilities for bank transfer payment methods."""

    pass
