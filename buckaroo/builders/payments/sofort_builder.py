from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class SofortBuilder(PaymentBuilder, BankTransferCapabilities):
    """Builder for Sofort payments with bank transfer capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for Sofort payments."""
        return "sofort"
    
    def country_code(self, country_code: str) -> 'SofortBuilder':
        """Set the Sofort country code."""
        return self.add_parameter("countrycode", country_code)
    
    def from_dict(self, data: Dict[str, Any]) -> 'SofortBuilder':
        """
        Populate the Sofort builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            SofortBuilder: Self for method chaining
            
        Additional Sofort-specific keys:
            - country_code: Sofort country code (str)
        """
        # Call parent from_dict first
        super().from_dict(data)
        
        # Handle Sofort-specific parameters
        if 'country_code' in data:
            self.country_code(data['country_code'])
            
        return self
    
    # Bank transfer capabilities (inherited from BankTransferCapabilities):
    # - instant_refund() 
    # - pay_fast_checkout()
    # 
    # Standard methods (inherited from PaymentBuilder):
    # - pay(), refund(), capture(), cancel(), execute_action()
    
    # Optional: Create aliases with method names for consistency
    def payFastCheckout(self) -> PaymentResponse:
        """Enable PayFast Checkout for Sofort payments."""
        return self.pay_fast_checkout()
    
    def instantRefund(self) -> PaymentResponse:
        """Initiate an instant refund for Sofort payments."""
        return self.instant_refund()