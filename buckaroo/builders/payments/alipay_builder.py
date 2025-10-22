
from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class AlipayBuilder(PaymentBuilder):
    """Builder for Alipay payments."""
    
    def get_service_name(self) -> str:
        """Get the service name for Alipay payments."""
        return "alipay"
    
    def use_mobile_view(self, value: bool) -> 'AlipayBuilder':
        """Set the mobile view preference."""
        return self.add_parameter("usemobileview", value)
    
    def from_dict(self, data: Dict[str, Any]) -> 'AlipayBuilder':
        """
        Populate the Alipay builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            AlipayBuilder: The updated AlipayBuilder instance
        """
        super().from_dict(data)
        
        self.use_mobile_view(data.get("usemobileview", False))

        return self