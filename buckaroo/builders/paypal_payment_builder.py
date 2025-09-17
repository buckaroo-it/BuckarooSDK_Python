from typing import Dict, Any
from .payment_builder import PaymentBuilder


class PaypalPaymentBuilder(PaymentBuilder):
    """Builder for PayPal payments."""
    
    def get_service_name(self) -> str:
        """Get the service name for PayPal payments."""
        return "paypal"