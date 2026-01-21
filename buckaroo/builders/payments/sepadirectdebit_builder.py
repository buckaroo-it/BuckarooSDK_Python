from typing import Dict, Any
from .payment_builder import PaymentBuilder

class SepaDirectDebitBuilder(PaymentBuilder):
    """Builder for Sepa Direct Debit payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Sepa Direct Debit payments."""
        return "SepaDirectDebit"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Sepa Direct Debit payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "customeraccountname": {"type": str, "required": True, "description": "Customer account name"},
                "customeriban": {"type": str, "required": True, "description": "Customer IBAN"},
                "customerbic": {"type": str, "required": False, "description": "Customer BIC"},
                "collectdate": {"type": str, "required": False, "description": "Collect date"},
                "mandateReference": {"type": str, "required": False, "description": "Mandate reference"},
                "mandateDate": {"type": str, "required": False, "description": "Mandate date"},
                "startRecurrent": {"type": str, "required": False, "description": "Start recurrent"},
                "electronicSignature": {"type": str, "required": False, "description": "Electronic signature"},
            }

        return {}