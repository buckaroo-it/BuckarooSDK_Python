


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class MultibancoBuilder(PaymentBuilder):
    """Builder for Multibanco payments."""

    def get_service_name(self) -> str:
        """Get the service name for Multibanco payments."""
        return "Multibanco"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Multibanco payments based on action."""

        return {}
