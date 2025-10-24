


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class DefaultBuilder(PaymentBuilder):
    """Builder for Default payments."""

    def get_service_name(self) -> str:
        """Get the service name for Default payments."""
        # Try to get method from payload, fallback to 'Unknown' if not available
        return self._payload.get('method', 'Unknown')
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Default payments based on action."""

        return {}
