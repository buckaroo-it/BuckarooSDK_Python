


from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class BancontactBuilder(PaymentBuilder):
    """Builder for Bancontact payments."""

    def get_service_name(self) -> str:
        """Get the service name for bancontactmrcash payments."""
        return "bancontactmrcash"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Bancontact payments based on action."""
        
        if action.lower() in ["pay", "authenticate"]:
            return {
                "savetoken": {"type": str, "required": False, "description": "Save payment token for future use"},
            }
        
        if action.lower() in ["payEncrypted", "completePayment"]:
            return {
                "encryptedCardData": {"type": str, "required": True, "description": "Encrypted card data for payment"},
            }

        
        if action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require additional parameters
            return {}
        
        return {}
