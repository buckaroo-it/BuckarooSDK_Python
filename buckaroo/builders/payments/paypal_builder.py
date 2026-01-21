from typing import Dict, Any
from .payment_builder import PaymentBuilder

class PaypalBuilder(PaymentBuilder):
    """Builder for Paypal payments with bank transfer capabilities."""

    def get_service_name(self) -> str:
        """Get the service name for Paypal payments."""
        return "paypal"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Paypal payments based on action."""
        
        if action.lower() in ["pay"]:
            return {
                "buyerEmail": {"type": str, "required": False, "description": "Buyer's email address."},
                "productName": {"type": str, "required": False, "description": "Name of the product."},
                "billingAgreementDescription": {"type": str, "required": False, "description": "Description of the billing agreement."},
                "pageStyle": {"type": str, "required": False, "description": "Style of the payment page."},
                "startrecurrent": {"type": str, "required": False, "description": "Start of recurrent payment."},
                "payPalOrderId": {"type": str, "required": False, "description": "PayPal order ID."},
            }

        return {}