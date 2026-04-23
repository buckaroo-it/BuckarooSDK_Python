from __future__ import annotations
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
        return self._payload.get("brand", "CreditCard")

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Credit Card payments based on action."""
        action_lower = action.lower()

        if action_lower == "payencrypted":
            return {"encryptedcarddata": {"type": str, "required": True, "description": "Encrypted card data"}}

        if action_lower == "paywithsecuritycode":
            return {"encryptedsecuritycode": {"type": str, "required": True, "description": "Encrypted security code"}}

        if action_lower in ("paywithtoken", "authorizewithtoken"):
            return {"sessionid": {"type": str, "required": True, "description": "Session ID token from Hosted Fields submitSession()"}}

        return {}

    def payWithSecurityCode(self, validate: bool = True) -> PaymentResponse:
        """Process a payment with a security code."""
        return self.execute_action("PayWithSecurityCode", validate=validate)

    def payWithToken(self, validate: bool = True) -> PaymentResponse:
        """Process a payment using a Hosted Fields session token.

        Set the SessionId parameter via add_parameter('SessionId', token) before calling.
        The token comes from the Hosted Fields submitSession() call on the client side.
        The response may include a RequiredAction for 3DS authentication.
        """
        return self.execute_action("PayWithToken", validate=validate)

    def authorizeWithToken(self, validate: bool = True) -> PaymentResponse:
        """Authorize a payment using a Hosted Fields session token.

        Set the SessionId parameter via add_parameter('SessionId', token) before calling.
        The response may include a RequiredAction for 3DS authentication.
        """
        return self.execute_action("AuthorizeWithToken", validate=validate)

    def payRecurrent(self, validate: bool = True) -> PaymentResponse:
        """Execute a recurring payment against a previously stored token."""
        return self.execute_action("PayRecurrent", validate=validate)
