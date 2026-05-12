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

        if action.lower() == "payencrypted":
            # Encrypted payment uses encrypted data instead of raw card details
            return {
                "encryptedcarddata": {
                    "type": str,
                    "required": True,
                    "description": "Encrypted card data",
                },
            }

        if action.lower() == "paywithsecuritycode":
            # Payment with security code uses encrypted data instead of raw card details
            return {
                "encryptedsecuritycode": {
                    "type": str,
                    "required": True,
                    "description": "Encrypted security code",
                },
            }

        if action.lower() == "paywithtoken":
            # Hosted Fields inline payment: token from submitSession()
            return {
                "sessionid": {
                    "type": str,
                    "required": True,
                    "description": "Session ID token from Hosted Fields submitSession()",
                },
            }

        if action.lower() == "authorizewithtoken":
            # Hosted Fields inline authorize: token from submitSession()
            return {
                "sessionid": {
                    "type": str,
                    "required": True,
                    "description": "Session ID token from Hosted Fields submitSession()",
                },
            }

        return {}

    def payWithSecurityCode(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
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

    def payWithToken(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        """
        Process a payment using a Hosted Fields session token.

        The SessionId parameter must be set via add_parameter('SessionId', token)
        before calling this method. The token comes from the Hosted Fields
        submitSession() call on the client side.

        The response may include a RequiredAction for 3DS authentication.
        """
        payment_request = self.build("PayWithToken", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)

    def authorizeWithToken(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        """
        Authorize a payment using a Hosted Fields session token.

        The SessionId parameter must be set via add_parameter('SessionId', token)
        before calling this method. The token comes from the Hosted Fields
        submitSession() call on the client side.

        The response may include a RequiredAction for 3DS authentication.
        """
        payment_request = self.build("AuthorizeWithToken", validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)

    def payRecurrent(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
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
