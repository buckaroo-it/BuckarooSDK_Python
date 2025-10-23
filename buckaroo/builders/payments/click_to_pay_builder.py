


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class ClickToPayBuilder(PaymentBuilder):
    """Builder for Click to Pay payments."""

    def get_service_name(self) -> str:
        """Get the service name for Click to Pay payments."""
        return "ClickToPay"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Click to Pay payments based on action."""

        return {}
