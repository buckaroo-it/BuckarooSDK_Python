


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
        
        # Common parameters for all actions
        common_params = {
            "savetoken": {"type": str, "required": False, "description": "Save payment token for future use"},
        }
        
        if action.lower() in ["pay"]:
            return {
                **common_params,
                # Add any Pay-specific parameters here
            }
        elif action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require additional parameters
            return {}
        else:
            # Default to common parameters
            return common_params
    
    def savetoken(self, savetoken: str) -> 'BancontactBuilder':
        """Set the save token."""
        return self.add_parameter("savetoken", savetoken)
    
    def from_dict(self, data: Dict[str, Any]) -> 'BancontactBuilder':
        """
        Populate the Bancontact builder from a dictionary of parameters.

        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            BancontactBuilder: The updated BancontactBuilder instance
        """
        super().from_dict(data)

        # Handle SaveToken parameter (case-insensitive)
        save_token = data.get("SaveToken") or data.get("savetoken")

        if isinstance(save_token, str):
            self.savetoken(save_token)

        return self