from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class PayconiqBuilder(PaymentBuilder, BankTransferCapabilities):
    """Builder for Payconiq payments with bank transfer capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for Payconiq payments."""
        return "payconiq"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Payconiq payments based on action."""
        
        if action.lower() in ["pay", "payfastcheckout"]:
            return {
                "mobilenumber": {"type": str, "required": False, "description": "Mobile number for Payconiq"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
                "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
            }
        elif action.lower() == "instantrefund":
            # Instant refund has different requirements
            return {}
        elif action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require mobile number
            return {}
        else:
            # Default to Pay action parameters
            return {
                "mobilenumber": {"type": str, "required": False, "description": "Mobile number for Payconiq"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
                "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
            }
    
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
    def payFastCheckout(self, validate: bool = True) -> PaymentResponse:
        """Enable PayFast Checkout for Payconiq payments."""
        return self.pay_fast_checkout(validate=validate)
    
    def instantRefund(self, validate: bool = True) -> PaymentResponse:
        """Initiate an instant refund for Payconiq payments."""
        return self.instant_refund(validate=validate)