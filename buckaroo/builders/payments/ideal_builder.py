from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class IdealBuilder(PaymentBuilder, BankTransferCapabilities):
    """Builder for iDEAL payments with bank transfer capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for iDEAL payments."""
        return "ideal"
    
    def issuer(self, issuer: str) -> 'IdealBuilder':
        """Set the iDEAL issuer."""
        return self.add_parameter("issuer", issuer)
    
    def from_dict(self, data: Dict[str, Any]) -> 'IdealBuilder':
        """
        Populate the iDEAL builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            IdealBuilder: Self for method chaining
            
        Additional iDEAL-specific keys:
            - issuer: iDEAL bank issuer code (str)
        """
        # Call parent from_dict first
        super().from_dict(data)
        
        # Handle iDEAL-specific parameters

        if 'issuer' in data:
            self.issuer(data['issuer'])
            
        return self
    
    def payFastCheckout(self) -> PaymentResponse:
        """Enable PayFast Checkout for iDEAL payments."""
        return self.pay_fast_checkout()  # From BankTransferCapabilities
    
    def instantRefund(self) -> PaymentResponse:
        """Initiate an instant refund for iDEAL payments."""
        return self.instant_refund()  # From BankTransferCapabilities