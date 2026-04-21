from typing import Dict, Any
from .payment_builder import PaymentBuilder


class WeroBuilder(PaymentBuilder):
    """Builder for Wero payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Wero payments."""
        return "Wero"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Wero payments based on action."""

        if action.lower() in ["pay"]:
            return {}

        return {}
