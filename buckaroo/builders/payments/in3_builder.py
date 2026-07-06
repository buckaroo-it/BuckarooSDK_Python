from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.authorize_capture_capable import AuthorizeCaptureCapable


class In3Builder(PaymentBuilder, AuthorizeCaptureCapable):
    """Builder for IN3 payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for IN3 payments."""
        return "in3"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for IN3 payments based on action."""

        if action.lower() in ["pay", "authorize"]:
            params = {
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
                "article": {"type": list, "required": True, "description": "IN3 articles"},
            }

            # Authorize is only used for the ABN AMRO "Zakelijk op rekening"
            # (business-on-account) flow, which the gateway routes via the
            # required Route parameter (e.g. "abn_b2b"). Pay does not use it.
            if action.lower() == "authorize":
                params["route"] = {
                    "type": str,
                    "required": True,
                    "description": 'Financing route, e.g. "abn_b2b" for ABN AMRO business',
                }

            return params

        return {}
