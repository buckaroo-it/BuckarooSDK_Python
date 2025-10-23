


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class BlikBuilder(PaymentBuilder):
    """Builder for Blik payments."""

    def get_service_name(self) -> str:
        """Get the service name for Blik payments."""
        return "Blik"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Blik payments based on action."""

        return {}
