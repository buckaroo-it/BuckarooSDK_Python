from typing import Dict, Any
from .payment_builder import PaymentBuilder


class In3Builder(PaymentBuilder):
    """Builder for IN3 payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for IN3 payments."""
        return "in3"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for IN3 payments based on action."""

        if action.lower() in ["pay"]:
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
                "article": {"type": list, "required": True, "description": "IN3 articles"},
            }

        return {}
