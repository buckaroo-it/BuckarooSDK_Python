from typing import Dict, Any
from .payment_builder import PaymentBuilder


class KBCBuilder(PaymentBuilder):
    """Builder for KBC payments."""

    def get_service_name(self) -> str:
        """Get the service name for KBC payments."""
        return "KBCPaymentButton"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for KBC payments based on action."""

        return {}
