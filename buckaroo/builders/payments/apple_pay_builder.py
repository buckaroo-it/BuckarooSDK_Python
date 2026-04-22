from typing import Dict, Any
from .payment_builder import PaymentBuilder


class ApplePayBuilder(PaymentBuilder):
    """Builder for Apple Pay payments."""

    def get_service_name(self) -> str:
        """Get the service name for apple pay payments."""
        return "applepay"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Apple Pay payments based on action."""

        if action.lower() in ["pay"]:
            return {
                "PaymentData": {
                    "type": str,
                    "required": True,
                    "description": "Apple Pay payment data",
                },
                "CustomerCardName": {
                    "type": str,
                    "required": False,
                    "description": "Customer card name",
                },
            }

        # Default to Pay action parameters
        return {}
