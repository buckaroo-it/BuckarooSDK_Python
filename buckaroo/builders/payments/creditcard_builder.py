from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities import AuthorizeCapable
from ...models.payment_response import PaymentResponse

class CreditcardBuilder(PaymentBuilder, AuthorizeCapable):
    """Builder for Credit Card payments with authorization capabilities."""
    
    def get_service_name(self) -> str:
        """Get the service name for Creditcard payments."""
        return "creditcard"
    
    def card_number(self, card_number: str) -> 'CreditcardBuilder':
        """Set the credit card number."""
        return self.add_parameter("cardnumber", card_number)
    
    def expiry_date(self, expiry_date: str) -> 'CreditcardBuilder':
        """Set the card expiry date (MM/YY format)."""
        return self.add_parameter("expirydate", expiry_date)
    
    def cvc(self, cvc: str) -> 'CreditcardBuilder':
        """Set the card CVC/CVV code."""
        return self.add_parameter("cvc", cvc)
    
    def cardholder_name(self, name: str) -> 'CreditcardBuilder':
        """Set the cardholder name."""
        return self.add_parameter("cardholdername", name)
    
    def from_dict(self, data: Dict[str, Any]) -> 'CreditcardBuilder':
        """
        Populate the Creditcard builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            CreditcardBuilder: Self for method chaining

        Additional Creditcard-specific keys:
            - card_number: Card number for Creditcard (str)
            - expiry_date: Card expiry date MM/YY (str)
            - cvc: Card CVC for Creditcard (str)
            - cardholder_name: Name on the card (str)
        """
        # Call parent from_dict first
        super().from_dict(data)
        
        # Handle credit card specific parameters
        if 'card_number' in data:
            self.card_number(data['card_number'])
            
        if 'expiry_date' in data:
            self.expiry_date(data['expiry_date'])
            
        if 'cvc' in data:
            self.cvc(data['cvc'])
            
        if 'cardholder_name' in data:
            self.cardholder_name(data['cardholder_name'])
            
        return self
    
    # Credit card specific methods (inherited from AuthorizeCapable):
    # - authorize() - Authorize payment without capture
    # 
    # Standard methods (inherited from PaymentBuilder):
    # - pay() - Standard payment
    # - refund() - Standard refund (not instant)
    # - capture() - Capture authorized payment
    # - cancel() - Cancel transaction