from __future__ import annotations
from typing import Dict, Any

from buckaroo.models.payment_response import PaymentResponse
from .payment_builder import PaymentBuilder


class KlarnaKPBuilder(PaymentBuilder):
    """Builder for Klarna KP payments with bank transfer capabilities."""

    def required_fields(self, action: str = "Pay") -> Dict[str, Any]:
        if action.lower() == "reserve":
            return {
                "currency": self._currency,
                "invoice": self._invoice,
            }

        return {}

    def get_service_name(self) -> str:
        """Get the service name for Klarna KP payments."""
        return "klarnakp"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Klarna KP payments based on action."""

        if action.lower() in ["pay", "cancelreservation", "extendreservation"]:
            return {
                "reservationNumber": {
                    "type": str,
                    "required": True,
                    "description": "Klarna KP reservation number",
                },
            }

        if action.lower() == "reserve":
            return {
                "operatingCountry": {
                    "type": str,
                    "required": True,
                    "description": "Operating country code",
                },
                "article": {"type": list, "required": True, "description": "Klarna KP articles"},
            }

        if action.lower() == "updatereservation":
            return {
                "reservationNumber": {
                    "type": str,
                    "required": True,
                    "description": "Klarna KP reservation number",
                },
                "article": {"type": list, "required": True, "description": "Klarna KP articles"},
            }

        if action.lower() == "addshippinginfo":
            return {
                "originalTransactionKey": {
                    "type": str,
                    "required": True,
                    "description": "Original transaction key",
                },
                "shippingMethod": {
                    "type": str,
                    "required": False,
                    "description": "Shipping method",
                },
                "company": {"type": str, "required": False, "description": "Shipping company name"},
                "trackingNumber": {
                    "type": str,
                    "required": False,
                    "description": "Shipping tracking number",
                },
            }

        return {}

    def reserve(self, validate: bool = True) -> PaymentResponse:
        """Create a Klarna KP reservation."""
        return self._post_data_request(self.build("Reserve", validate=validate).to_dict())

    def cancelReservation(self, validate: bool = True) -> PaymentResponse:
        """Cancel a Klarna KP reservation."""
        return self._post_data_request(self.build("CancelReservation", validate=validate).to_dict())

    def updateReservation(self, validate: bool = True) -> PaymentResponse:
        """Update a Klarna KP reservation."""
        return self._post_data_request(self.build("UpdateReservation", validate=validate).to_dict())

    def extendReservation(self, validate: bool = True) -> PaymentResponse:
        """Extend a Klarna KP reservation."""
        return self._post_data_request(self.build("ExtendReservation", validate=validate).to_dict())

    def addShippingInfo(self, validate: bool = True) -> PaymentResponse:
        """Add shipping information to a Klarna KP order."""
        return self._post_data_request(self.build("AddShippingInfo", validate=validate).to_dict())
