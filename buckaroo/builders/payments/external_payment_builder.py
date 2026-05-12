from typing import Any, Dict

from .payment_builder import PaymentBuilder


class ExternalPaymentBuilder(PaymentBuilder):
    """Builder for External payments."""

    def get_service_name(self) -> str:
        """Get the service name for External payments."""
        return "ExternalPayment"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """External payments declare no service-level parameters."""
        return {}
