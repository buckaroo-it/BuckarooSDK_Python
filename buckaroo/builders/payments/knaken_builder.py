


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class KnakenBuilder(PaymentBuilder):
    """Builder for Knaken payments."""

    def get_service_name(self) -> str:
        """Get the service name for Knaken payments."""
        return "Knaken"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Knaken payments based on action."""

        return {}
