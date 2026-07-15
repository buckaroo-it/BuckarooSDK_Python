from __future__ import annotations
from typing import Dict, Any
from ...models.payment_response import PaymentResponse
from .payment_builder import PaymentBuilder


class IdinBuilder(PaymentBuilder):
    """Builder for iDIN identification, age verification, and login.

    iDIN lets Dutch banks confirm a consumer's identity on the merchant's
    behalf. Every action is a DataRequest keyed on a single ``issuerId``
    (BIC code of the consumer's bank) service parameter:

    - ``identify()``: full identification, returns the bank-registered
      customer details on the async push.
    - ``verify()``: age verification (18+).
    - ``login()``: returns a unique consumer ID for login purposes.

    The immediate response only carries ``Status`` and the redirect
    (``RequiredAction.RedirectURL``); the bank's personal data arrives later
    via push and is already parseable by the existing :class:`PaymentResponse`.
    """

    def required_fields(self, action: str = "identify") -> Dict[str, Any]:
        """
        Get the required fields for this payment method.

        iDIN carries no amount or currency; only the ReturnURL family is
        required.

        Returns:
            Dict[str, Any]: Dictionary mapping field names to their current values
        """
        return {
            "return_url": self._return_url,
            "return_url_cancel": self._return_url_cancel,
            "return_url_error": self._return_url_error,
            "return_url_reject": self._return_url_reject,
        }

    def get_service_name(self) -> str:
        """Get the service name for iDIN requests."""
        return "Idin"

    def get_allowed_service_parameters(self, action: str = "identify") -> Dict[str, Any]:
        """Get the allowed service parameters for iDIN requests based on action."""

        if action.lower() in ["identify", "verify", "login"]:
            return {
                "issuerId": {
                    "type": str,
                    "required": True,
                    "description": "BIC code of the issuing bank of the consumer",
                },
            }

        return {}

    def identify(self, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        """Request full identification from the consumer's bank."""
        payment_request = self.build(
            "identify", validate=validate, strict_validation=strict_validation
        )
        return self._post_data_request(payment_request.to_dict())

    def verify(self, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        """Verify whether the consumer is 18 years or older."""
        payment_request = self.build(
            "verify", validate=validate, strict_validation=strict_validation
        )
        return self._post_data_request(payment_request.to_dict())

    def login(self, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        """Request a unique consumer ID for login purposes."""
        payment_request = self.build(
            "login", validate=validate, strict_validation=strict_validation
        )
        return self._post_data_request(payment_request.to_dict())
