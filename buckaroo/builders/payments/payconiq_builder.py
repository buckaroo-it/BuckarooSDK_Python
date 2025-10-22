from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class PayconiqBuilder(PaymentBuilder, BankTransferCapabilities):
    """Builder for Payconiq payments with bank transfer capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for Payconiq payments."""
        return "payconiq"
    
    def mobile_number(self, mobile_number: str) -> 'PayconiqBuilder':
        """Set the mobile number for Payconiq."""
        return self.add_parameter("mobilenumber", mobile_number)
    
    def from_dict(self, data: Dict[str, Any]) -> 'PayconiqBuilder':
        """
        Populate the Payconiq builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            PayconiqBuilder: Self for method chaining
            
        Additional Payconiq-specific keys:
            - mobile_number: Mobile number for Payconiq (str)
        """
        # Call parent from_dict first
        super().from_dict(data)
        
        # Handle Payconiq-specific parameters
        if 'mobile_number' in data:
            self.mobile_number(data['mobile_number'])
            
        return self
    
    # Bank transfer capabilities (inherited from BankTransferCapabilities):
    # - instant_refund() 
    # - pay_fast_checkout()
    # 
    # Standard methods (inherited from PaymentBuilder):
    # - pay(), refund(), capture(), cancel(), execute_action()
    
    # Optional: Create aliases with method names for consistency
    def payFastCheckout(self) -> PaymentResponse:
        """Enable PayFast Checkout for Payconiq payments."""
        return self.pay_fast_checkout()
    
    def instantRefund(self) -> PaymentResponse:
        """Initiate an instant refund for Payconiq payments."""
        return self.instant_refund()