from typing import Dict, Any
from .payment_builder import PaymentBuilder

class VoucherBuilder(PaymentBuilder):
    """Builder for Voucher payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Voucher payments."""
        return self._payload.get('voucher_name', 'Vouchers')
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Voucher payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "article": {"type": list, "required": True, "description": "Articles"},
            }

        return {}