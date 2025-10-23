
from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class ApplePayBuilder(PaymentBuilder):
    """Builder for Apple Pay payments."""

    def get_service_name(self) -> str:
        """Get the service name for apple pay payments."""
        return "applepay"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Apple Pay payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "PaymentData": {"type": str, "required": True, "description": "Apple Pay payment data"},
                "paymentdata": {"type": str, "required": True, "description": "Apple Pay payment data (lowercase)"},
                "CustomerCardName": {"type": str, "required": False, "description": "Customer card name"},
                "customercardname": {"type": str, "required": False, "description": "Customer card name (lowercase)"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
            }
        elif action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require payment data
            return {}
        else:
            # Default to Pay action parameters
            return {
                "PaymentData": {"type": str, "required": True, "description": "Apple Pay payment data"},
                "paymentdata": {"type": str, "required": True, "description": "Apple Pay payment data (lowercase)"},
                "CustomerCardName": {"type": str, "required": False, "description": "Customer card name"},
                "customercardname": {"type": str, "required": False, "description": "Customer card name (lowercase)"},
                "savetoken": {"type": (str, bool), "required": False, "description": "Save payment token for future use"},
            }
    
    def payment_data(self, value: str) -> 'ApplePayBuilder':
        """Set the payment data."""
        return self.add_parameter("PaymentData", value)
    
    def customer_card_name(self, value: str) -> 'ApplePayBuilder':
        """Set the customer card name."""
        return self.add_parameter("CustomerCardName", value)

    def from_dict(self, data: Dict[str, Any]) -> 'ApplePayBuilder':
        """
        Populate the Apple Pay builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            ApplePayBuilder: The updated ApplePayBuilder instance
        """
        super().from_dict(data)

        # Handle CustomerCardName parameter (case-insensitive)
        payment_data = data.get("PaymentData") or data.get("paymentdata")
        if isinstance(payment_data, str):
            self.payment_data(payment_data)

        customer_card_name = data.get("CustomerCardName") or data.get("customercardname")
        if isinstance(customer_card_name, str):
            self.customer_card_name(customer_card_name)

        return self