from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class PayByBankBuilder(PaymentBuilder, BankTransferCapabilities):
    """Builder for PayByBank payments with bank transfer capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for PayByBank payments."""
        return "PayByBank"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for PayByBank payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "issuer": {"type": str, "required": True, "description": "PayByBank bank issuer code"},
            }

        return {}