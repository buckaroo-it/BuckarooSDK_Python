


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class BelfiusBuilder(PaymentBuilder):
    """Builder for Belfius payments."""

    def get_service_name(self) -> str:
        """Get the service name for belfius payments."""
        return "belfius"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Belfius payments based on action."""

        return {}
