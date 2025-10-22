
"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from typing import TYPE_CHECKING
from ....models.payment_response import PaymentResponse

if TYPE_CHECKING:
    from ..payment_builder import PaymentBuilder

class AuthorizeCapable:
    """Mixin for payment methods that support authorization (Credit Card)."""
    
    def authorize(self: 'PaymentBuilder') -> PaymentResponse:
        """
        Authorize a payment without capturing it.
        
        Available for: Credit Card
        Not available for: iDEAL, Sofort, PayConiq (immediate transfer)
        
        Returns:
            PaymentResponse: The authorization response
        """
        payment_request = self.build("Authorize")
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)