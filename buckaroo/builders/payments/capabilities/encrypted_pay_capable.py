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

class EncryptedPayCapable:
    """Mixin for payment methods that support encryption (Credit Card)."""

    def payEncrypted(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """
        Process a payment with encryption.

        Available for: Credit Card
        Not available for: iDEAL, Sofort, PayConiq (immediate transfer)

        Args:
            validate (bool): Whether to validate service parameters before building

        Returns:
            PaymentResponse: The payment response
        """
        payment_request = self.build("PayEncrypted", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)