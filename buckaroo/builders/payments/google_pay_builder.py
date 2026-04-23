from typing import Dict, Any
from .payment_builder import PaymentBuilder


class GooglePayBuilder(PaymentBuilder):
    """Builder for Giftcards payments."""

    def get_service_name(self) -> str:
        """Get the service name for Google Pay payments."""
        return "GooglePay"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Google Pay payments based on action."""

        if action.lower() in ["pay"]:
            return {
                "PaymentData": {"type": str, "required": True, "description": ""},
                "CustomerCardName": {"type": str, "required": False, "description": ""},
            }

        return {}
