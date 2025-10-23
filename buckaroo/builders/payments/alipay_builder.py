
from typing import Dict, Any
from .payment_builder import PaymentBuilder

class AlipayBuilder(PaymentBuilder):
    """Builder for Alipay payments."""
    
    def get_service_name(self) -> str:
        """Get the service name for Alipay payments."""
        return "Alipay"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Alipay payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "UseMobileView": {"type": (str, bool), "required": True, "description": "Use mobile view for Alipay"}
            }

        # Default to Pay action parameters
        return {
        }