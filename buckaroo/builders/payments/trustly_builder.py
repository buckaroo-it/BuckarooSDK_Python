from typing import Dict, Any
from .payment_builder import PaymentBuilder


class TrustlyBuilder(PaymentBuilder):
    """Builder for Trustly payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Trustly payments."""
        return "Trustly"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Trustly payments based on action."""

        if action.lower() in ["pay"]:
            return {
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
                "customerCountryCode": {
                    "type": str,
                    "required": True,
                    "description": "Customer country code",
                },
                "consumeremail": {"type": str, "required": True, "description": "Customer email"},
            }

        return {}
