from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class IdealBuilder(PaymentBuilder, BankTransferCapabilities):
    """Builder for iDEAL payments with bank transfer capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for iDEAL payments."""
        return "ideal"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for iDEAL payments based on action."""
        
        if action.lower() in ["pay", "payfastcheckout"]:
            return {
                "issuer": {"type": str, "required": True, "description": "iDEAL bank issuer code"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
                "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
            }
        elif action.lower() == "instantrefund":
            # Instant refund has different requirements
            return {
                "issuer": {"type": str, "required": False, "description": "iDEAL bank issuer code"},
            }
        elif action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require issuer
            return {}
        else:
            # Default to Pay action parameters
            return {
                "issuer": {"type": str, "required": True, "description": "iDEAL bank issuer code"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
                "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
            }
    
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
    
    def payFastCheckout(self, validate: bool = True) -> PaymentResponse:
        """Enable PayFast Checkout for iDEAL payments."""
        return self.pay_fast_checkout(validate=validate)  # From BankTransferCapabilities
    
    def instantRefund(self, validate: bool = True) -> PaymentResponse:
        """Initiate an instant refund for iDEAL payments."""
        return self.instant_refund(validate=validate)  # From BankTransferCapabilities