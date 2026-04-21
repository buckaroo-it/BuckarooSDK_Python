from typing import Dict, Any
from .payment_builder import PaymentBuilder


class Przelewy24Builder(PaymentBuilder):
    """Builder for Przelewy24 payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Przelewy24 payments."""
        return "przelewy24"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Przelewy24 payments based on action."""

        if action.lower() in ["pay"]:
            return {
                "customerEmail": {
                    "type": str,
                    "required": True,
                    "description": "Customer email address",
                },
                "customerFirstName": {
                    "type": str,
                    "required": True,
                    "description": "Customer first name",
                },
                "customerLastName": {
                    "type": str,
                    "required": True,
                    "description": "Customer last name",
                },
            }

        return {}
