from typing import Dict, Any
from .payment_builder import PaymentBuilder


class EpsBuilder(PaymentBuilder):
    """Builder for EPS payments."""

    def get_service_name(self) -> str:
        """Get the service name for EPS payments."""
        return "EPS"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for EPS payments based on action."""

        return {}
