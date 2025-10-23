


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class BizumBuilder(PaymentBuilder):
    """Builder for Bizum payments."""

    def get_service_name(self) -> str:
        """Get the service name for bizum payments."""
        return "Bizum"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Bizum payments based on action."""

        return {}
