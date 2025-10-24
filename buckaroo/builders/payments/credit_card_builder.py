from typing import Dict, Any

from buckaroo.builders.payments.capabilities.encrypted_pay_capable import EncryptedPayCapable
from .payment_builder import PaymentBuilder
from .capabilities.authorize_capture_capable import AuthorizeCaptureCapable
from ...models.payment_response import PaymentResponse

class CreditcardBuilder(PaymentBuilder, EncryptedPayCapable, AuthorizeCaptureCapable):
    """Builder for Credit Card payments with authorization capabilities."""
    
    _serviceName = "creditcard"
    
    def get_service_name(self) -> str:
        """Get the service name for Creditcard payments."""
        return self._payload.get('brand', 'CreditCard')

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Credit Card payments based on action."""

        if action.lower() == "payencrypted":
            # Encrypted payment uses encrypted data instead of raw card details
            return {
                "encryptedcarddata": {"type": str, "required": True, "description": "Encrypted card data"},
            }

        if action.lower() == "paywithsecuritycode":
            # Payment with security code uses encrypted data instead of raw card details
            return {
                "encryptedsecuritycode": {"type": str, "required": True, "description": "Encrypted security code"},
            }

        return {}
    
    def payWithSecurityCode(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """
        Process a payment with a security code.
        
        Args:
            validate (bool): Whether to validate service parameters before building

        Returns:
            PaymentResponse: The payment response
        """
        payment_request = self.build("PayWithSecurityCode", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)
    
    def payRecurrent(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        """
        PayRecurrent a previously authorized payment.
        
        Args:
            validate (bool): Whether to validate service parameters before building

        Returns:
            PaymentResponse: The payment response
        """
        
        payment_request = self.build("PayRecurrent", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)