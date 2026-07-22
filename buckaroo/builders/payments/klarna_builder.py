from __future__ import annotations
from typing import Dict, Any

from buckaroo.models.payment_response import PaymentResponse
from .payment_builder import PaymentBuilder


class KlarnaBuilder(PaymentBuilder):
    """Builder for Klarna MOR (Merchant of Record) payments.

    Klarna no longer returns a reservation number. Every follow-up action
    (CancelReservation, UpdateReservation, ExtendReservation, and Pay)
    references the prior Reserve through the Buckaroo ``DataRequestKey`` carried
    as a service parameter. The reservation actions post to ``/json/DataRequest``;
    Pay and Refund are transaction requests. Shipping details are attached to the
    Pay request (``shippingMethod`` / ``company`` / ``trackingNumber``); the
    gateway has no standalone AddShippingInfo action for this service.
    """

    def required_fields(self, action: str = "Pay") -> Dict[str, Any]:
        """Narrow the base required-field set per action.

        Reserve only needs currency + invoice; Pay needs currency + amount; the
        DataRequest follow-up actions need none of the base transaction fields.
        Refund and any other action fall through to the base requirements.
        """
        action = action.lower()

        if action == "reserve":
            return {
                "currency": self._currency,
                "invoice": self._invoice,
            }

        if action == "pay":
            return {
                "currency": self._currency,
                "amount_debit": self._amount_debit,
                "invoice": self._invoice,
            }

        if action in (
            "cancelreservation",
            "updatereservation",
            "extendreservation",
        ):
            return {}

        return super().required_fields(action)

    def get_service_name(self) -> str:
        """Get the service name for Klarna payments."""
        return "klarna"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Klarna payments based on action."""
        action = action.lower()

        if action == "pay":
            return {
                "dataRequestKey": {
                    "type": str,
                    "required": True,
                    "description": "Key of the prior Klarna Reserve",
                },
                "article": {
                    "type": list,
                    "required": False,
                    "description": "Articles to pay for on a partial delivery",
                },
                "shippingMethod": {
                    "type": str,
                    "required": False,
                    "description": "Shipping method",
                },
                "company": {
                    "type": str,
                    "required": False,
                    "description": "Shipping company name",
                },
                "trackingNumber": {
                    "type": str,
                    "required": False,
                    "description": "Shipping tracking number",
                },
            }

        if action == "reserve":
            return {
                "article": {
                    "type": list,
                    "required": True,
                    "description": "Klarna articles",
                },
                "operatingCountry": {
                    "type": str,
                    "required": True,
                    "description": "Operating country code",
                },
                "billingCustomer": {
                    "type": list,
                    "required": False,
                    "description": "Billing customer information",
                },
                "shippingCustomer": {
                    "type": list,
                    "required": False,
                    "description": "Shipping customer information",
                },
                "pno": {
                    "type": str,
                    "required": False,
                    "description": "Personal identification number",
                },
                "gender": {
                    "type": str,
                    "required": False,
                    "description": "Customer gender",
                },
                "locale": {
                    "type": str,
                    "required": False,
                    "description": "Customer locale",
                },
            }

        if action in ("cancelreservation", "extendreservation"):
            return {
                "dataRequestKey": {
                    "type": str,
                    "required": True,
                    "description": "Buckaroo data request key of the prior Reserve",
                },
            }

        if action == "updatereservation":
            return {
                "dataRequestKey": {
                    "type": str,
                    "required": True,
                    "description": "Buckaroo data request key of the prior Reserve",
                },
                "article": {
                    "type": list,
                    "required": False,
                    "description": "Updated Klarna articles",
                },
                "shippingCustomer": {
                    "type": list,
                    "required": False,
                    "description": "Updated shipping customer information",
                },
            }

        return {}

    def reserve(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        payment_request = self.build("Reserve", validate=validate)
        return self._post_data_request(payment_request.to_dict())

    def cancelReservation(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        payment_request = self.build("CancelReservation", validate=validate)
        return self._post_data_request(payment_request.to_dict())

    def updateReservation(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        payment_request = self.build("UpdateReservation", validate=validate)
        return self._post_data_request(payment_request.to_dict())

    def extendReservation(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:
        payment_request = self.build("ExtendReservation", validate=validate)
        return self._post_data_request(payment_request.to_dict())
