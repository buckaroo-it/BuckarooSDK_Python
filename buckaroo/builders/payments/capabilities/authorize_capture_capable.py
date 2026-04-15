from __future__ import annotations

"""
Payment capability mixins for specific payment features.

This module provides mixins that can be selectively applied to payment builders
based on their actual capabilities, rather than giving all methods to all builders.
"""

from typing import Optional, TYPE_CHECKING
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
    
    def cancelAuthorize(self: 'PaymentBuilder', original_transaction_key: Optional[str] = None, validate: bool = True) -> PaymentResponse:
        """
        Cancel a previously authorized payment.

        Uses AmountCredit (not AmountDebit) per Buckaroo API requirements.
        """
        txn_key = (
            original_transaction_key
            or self._payload.get('original_transaction_key')
            or self._payload.get('authorization_key')
        )
        if not txn_key:
            raise ValueError(
                "Original transaction key is required for cancelAuthorize "
                "(provide 'original_transaction_key' in payload)"
            )

        payment_request = self.build("CancelAuthorize", validate=validate)
        request_data = payment_request.to_dict()

        request_data['OriginalTransactionKey'] = txn_key

        # Buckaroo API requires AmountCredit for cancel-authorize, not AmountDebit
        if 'AmountDebit' in request_data:
            request_data['AmountCredit'] = request_data.pop('AmountDebit')

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
    