
"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from typing import TYPE_CHECKING
from ....models.payment_response import PaymentResponse

if TYPE_CHECKING:
    from ..payment_builder import PaymentBuilder

class AuthorizeCaptureCapable:
    """Mixin for payment methods that support authorization (Credit Card)."""
    
    def authorize(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """
        Authorize a payment without capturing it.
        
        Available for: Credit Card
        Not available for: iDEAL, Sofort, PayConiq (immediate transfer)
        
        Args:
            validate (bool): Whether to validate service parameters before building
        
        Returns:
            PaymentResponse: The authorization response
        """
        payment_request = self.build("Authorize", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)
    
    def authorizeEncrypted(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """
        Authorize a payment without capturing it.
        
        Available for: Credit Card
        Not available for: iDEAL, Sofort, PayConiq (immediate transfer)
        
        Args:
            validate (bool): Whether to validate service parameters before building
        
        Returns:
            PaymentResponse: The authorization response
        """
        payment_request = self.build("AuthorizeEncrypted", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)
    
    def capture(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """
        Capture a previously authorized payment.
        
        Args:
            validate (bool): Whether to validate service parameters before building

        Returns:
            PaymentResponse: The capture response
        """

        payment_request = self.build("Capture", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)
    