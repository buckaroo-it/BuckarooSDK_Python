from typing import Dict, Any
from .payment_builder import PaymentBuilder


class CreditCardPaymentBuilder(PaymentBuilder):
    """Builder for credit card payments."""
    
    def get_service_name(self) -> str:
        """Get the service name for credit card payments."""
        return "creditcard"
    
    def card_number(self, card_number: str) -> 'CreditCardPaymentBuilder':
        """Set the credit card number."""
        return self.add_parameter("cardNumber", card_number)
    
    def expiry_month(self, month: str) -> 'CreditCardPaymentBuilder':
        """Set the credit card expiry month."""
        return self.add_parameter("expiryMonth", month)
    
    def expiry_year(self, year: str) -> 'CreditCardPaymentBuilder':
        """Set the credit card expiry year."""
        return self.add_parameter("expiryYear", year)
    
    def cvv(self, cvv: str) -> 'CreditCardPaymentBuilder':
        """Set the credit card CVV."""
        return self.add_parameter("cvv", cvv)
    
    def from_dict(self, data: Dict[str, Any]) -> 'CreditCardPaymentBuilder':
        """
        Populate the credit card builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            CreditCardPaymentBuilder: Self for method chaining
            
        Additional credit card-specific keys:
            - card_number: Credit card number (str)
            - expiry_month: Card expiry month (str)
            - expiry_year: Card expiry year (str)
            - cvv: Card CVV code (str)
        """
        # Call parent from_dict first
        super().from_dict(data)
        
        # Handle credit card-specific parameters
        if 'card_number' in data:
            self.card_number(data['card_number'])
        if 'expiry_month' in data:
            self.expiry_month(data['expiry_month'])
        if 'expiry_year' in data:
            self.expiry_year(data['expiry_year'])
        if 'cvv' in data:
            self.cvv(data['cvv'])
            
        return self