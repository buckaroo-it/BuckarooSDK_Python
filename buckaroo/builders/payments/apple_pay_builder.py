
from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class ApplePayBuilder(PaymentBuilder):
    """Builder for Apple Pay payments."""

    def get_service_name(self) -> str:
        """Get the service name for apple pay payments."""
        return "applepay"
    
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