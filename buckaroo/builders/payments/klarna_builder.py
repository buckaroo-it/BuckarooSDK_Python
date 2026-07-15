from __future__ import annotations
from typing import Dict, Any, Optional

from buckaroo.models.payment_response import PaymentResponse
from .payment_builder import PaymentBuilder


class KlarnaBuilder(PaymentBuilder):
    """Builder for Klarna MOR (Merchant of Record) payments."""

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
            }

        if action == "reserve":
            return {
                "billingCustomer": {
                    "type": list,
                    "required": True,
                    "description": "Billing customer information",
                },
                "shippingCustomer": {
                    "type": list,
                    "required": True,
                    "description": "Shipping customer information",
                },
                "article": {
                    "type": list,
                    "required": True,
                    "description": "Klarna articles",
                },
                "operatingCountry": {
                    "type": str,
                    "required": False,
                    "description": "Operating country code",
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

        if action == "cancelreservation":
            return {}

        return {}

    def reserve(self: "PaymentBuilder", validate: bool = True) -> PaymentResponse:

        payment_request = self.build("Reserve", validate=validate)
        request_data = payment_request.to_dict()

        return self._post_data_request(request_data)

    def cancelReservation(
        self: "PaymentBuilder",
        original_transaction_key: Optional[str] = None,
        validate: bool = True,
    ) -> PaymentResponse:
        """Cancel a previously-reserved Klarna transaction.

        Mirrors :meth:`AuthorizeCaptureCapable.cancelAuthorize` but with the
        ``CancelReservation`` action.
        """
        txn_key = original_transaction_key or self._payload.get("original_transaction_key")
        if not txn_key:
            raise ValueError(
                "Original transaction key is required for cancelReservation "
                "(provide 'original_transaction_key' in payload)"
            )

        payment_request = self.build("CancelReservation", validate=validate)
        request_data = payment_request.to_dict()
        request_data["OriginalTransactionKey"] = txn_key

        return self._post_transaction(request_data)
