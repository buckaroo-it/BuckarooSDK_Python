from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.authorize_capable import AuthorizeCapable
from ...models.payment_response import PaymentResponse

class CreditcardBuilder(PaymentBuilder, AuthorizeCapable):
    """Builder for Credit Card payments with authorization capabilities."""
    
    _serviceName = "creditcard"
    
    def get_service_name(self) -> str:
        """Get the service name for Creditcard payments."""
        return self._serviceName

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Credit Card payments based on action."""
        
        # Common parameters for all actions
        common_params = {
            "savetoken": {"type": (str, bool), "required": False, "description": "Save card token for future use"},
            "cardtype": {"type": str, "required": False, "description": "Card type (visa, mastercard, etc.)"},
            "isrecurring": {"type": (str, bool), "required": False, "description": "Recurring payment flag"},
        }
        
        # Action-specific parameters
        if action.lower() in ["pay", "authorize"]:
            # Standard payment/authorization requires card details
            return {
                **common_params,
                "cardnumber": {"type": str, "required": True, "description": "Credit card number"},
                "expirydate": {"type": str, "required": True, "description": "Card expiry date (MM/YY format)"},
                "cvc": {"type": str, "required": True, "description": "Card CVC/CVV code"},
                "cardholdername": {"type": str, "required": False, "description": "Cardholder name"},
            }
        elif action.lower() == "payencrypted":
            # Encrypted payment uses encrypted data instead of raw card details
            return {
                **common_params,
                "encrypteddata": {"type": str, "required": True, "description": "Encrypted card data"},
                "cardholdername": {"type": str, "required": False, "description": "Cardholder name"},
            }
        elif action.lower() == "payrecurring":
            # Recurring payment uses token instead of card details
            return {
                **common_params,
                "cardtoken": {"type": str, "required": True, "description": "Saved card token"},
                "cardholdername": {"type": str, "required": False, "description": "Cardholder name"},
            }
        elif action.lower() in ["refund", "capture", "cancel"]:
            # These actions typically don't require card-specific parameters
            return {
                "savetoken": {"type": (str, bool), "required": False, "description": "Save card token for future use"},
            }
        else:
            # Default to Pay action parameters
            return {
                **common_params,
                "cardnumber": {"type": str, "required": True, "description": "Credit card number"},
                "expirydate": {"type": str, "required": True, "description": "Card expiry date (MM/YY format)"},
                "cvc": {"type": str, "required": True, "description": "Card CVC/CVV code"},
                "cardholdername": {"type": str, "required": False, "description": "Cardholder name"},
            }
    
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
    
    def encrypted_data(self, encrypted_data: str) -> 'CreditcardBuilder':
        """Set encrypted card data for PayEncrypted action."""
        return self.add_parameter("encrypteddata", encrypted_data)
    
    def card_token(self, token: str) -> 'CreditcardBuilder':
        """Set saved card token for recurring payments."""
        return self.add_parameter("cardtoken", token)
    
    def pay_encrypted(self, validate: bool = True) -> PaymentResponse:
        """Execute an encrypted payment."""
        return self.execute_action("PayEncrypted", validate=validate)
    
    def pay_recurring(self, validate: bool = True) -> PaymentResponse:
        """Execute a recurring payment using saved token."""
        return self.execute_action("PayRecurring", validate=validate)
    
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
            - encrypted_data: Encrypted card data for PayEncrypted action (str)
            - card_token: Saved card token for recurring payments (str)
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
            
        if 'encrypted_data' in data:
            self.encrypted_data(data['encrypted_data'])
            
        if 'card_token' in data:
            self.card_token(data['card_token'])
            
        return self
    
    # Credit card specific methods (inherited from AuthorizeCapable):
    # - authorize() - Authorize payment without capture
    # 
    # Standard methods (inherited from PaymentBuilder):
    # - pay() - Standard payment
    # - refund() - Standard refund (not instant)
    # - capture() - Capture authorized payment
    # - cancel() - Cancel transaction