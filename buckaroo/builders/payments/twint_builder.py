from typing import Dict, Any
from .payment_builder import PaymentBuilder


class TwintBuilder(PaymentBuilder):
    """Builder for Twint payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Twint payments."""
        return "Twint"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Twint payments based on action."""

        if action.lower() in ["pay"]:
            return {}

        return {}
