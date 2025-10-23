
from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class AlipayBuilder(PaymentBuilder):
    """Builder for Alipay payments."""
    
    def get_service_name(self) -> str:
        """Get the service name for Alipay payments."""
        return "Alipay"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Alipay payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "UseMobileView": {"type": (str, bool), "required": False, "description": "Use mobile view for Alipay"},
                "usemobileview": {"type": (str, bool), "required": False, "description": "Use mobile view for Alipay (lowercase)"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
            }
        elif action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require mobile view
            return {}
        else:
            # Default to Pay action parameters
            return {
                "UseMobileView": {"type": (str, bool), "required": False, "description": "Use mobile view for Alipay"},
                "usemobileview": {"type": (str, bool), "required": False, "description": "Use mobile view for Alipay (lowercase)"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
            }
    
    def use_mobile_view(self, value: bool) -> 'AlipayBuilder':
        """Set the mobile view preference."""
        return self.add_parameter("UseMobileView", value)
    
    def from_dict(self, data: Dict[str, Any]) -> 'AlipayBuilder':
        """
        Populate the Alipay builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            AlipayBuilder: The updated AlipayBuilder instance
        """
        super().from_dict(data)
        
        # Handle UseMobileView parameter (case-insensitive)
        use_mobile_view = data.get("UseMobileView") or data.get("usemobileview", False)
        if isinstance(use_mobile_view, str):
            use_mobile_view = use_mobile_view.lower() == "true"
        self.use_mobile_view(use_mobile_view)

        return self