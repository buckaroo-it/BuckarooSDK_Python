
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
    
    def pay_fast_checkout(self: 'PaymentBuilder') -> PaymentResponse:
        """
        Enable PayFast Checkout.
        
        Available for: iDEAL, Sofort, PayConiq
        Not available for: Credit Card, PayPal
        
        Returns:
            PaymentResponse: The fast checkout response
        """
        payment_request = self.build("payFastCheckout")
        
        request_data = payment_request.to_dict()

        return self._post_transaction(request_data)

