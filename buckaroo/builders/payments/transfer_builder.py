from typing import Dict, Any
from .payment_builder import PaymentBuilder

class TransferBuilder(PaymentBuilder):
    """Builder for Transfer payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Transfer payments."""
        return "Transfer"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Transfer payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "customeremail": {"type": str, "required": True, "description": "Customer email address"},
                "customerfirstname": {"type": str, "required": True, "description": "Customer first name"},
                "customerlastname": {"type": str, "required": True, "description": "Customer last name"},
                "customergender": {"type": str, "required": False, "description": "Customer gender"},
                "sendmail": {"type": bool, "required": False, "description": "Send email to customer"},
                "dateDue": {"type": str, "required": False, "description": "Due date for the transfer"},
                "customerCountry": {"type": str, "required": False, "description": "Customer country code"},
            }

        return {}