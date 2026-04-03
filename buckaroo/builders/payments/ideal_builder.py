from __future__ import annotations
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
                "issuer": {"type": str, "required": False, "description": "iDEAL bank issuer code"},
            }

        return {}