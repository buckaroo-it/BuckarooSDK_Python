from __future__ import annotations
from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class SofortBuilder(PaymentBuilder, BankTransferCapabilities):
    """Builder for Sofort payments with bank transfer capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for Sofort payments."""
        return "sofort"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Sofort payments based on action."""
        
        if action.lower() in ["pay", "payfastcheckout"]:
            return {
                "countrycode": {"type": str, "required": False, "description": "Sofort country code"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
                "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
            }
        elif action.lower() == "instantrefund":
            # Instant refund has different requirements
            return {}
        elif action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require country code
            return {}
        else:
            # Default to Pay action parameters
            return {
                "countrycode": {"type": str, "required": False, "description": "Sofort country code"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
                "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
            }
    
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
    def payFastCheckout(self, validate: bool = True) -> PaymentResponse:
        """Enable PayFast Checkout for Sofort payments."""
        return self.pay_fast_checkout(validate=validate)
    
    def instantRefund(self, validate: bool = True) -> PaymentResponse:
        """Initiate an instant refund for Sofort payments."""
        return self.instant_refund(validate=validate)