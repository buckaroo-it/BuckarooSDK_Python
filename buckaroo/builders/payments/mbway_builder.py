


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class MBWayBuilder(PaymentBuilder):
    """Builder for MBWay payments."""

    def get_service_name(self) -> str:
        """Get the service name for MBWay payments."""
        return "MBWay"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for MBWay payments based on action."""

        return {}
