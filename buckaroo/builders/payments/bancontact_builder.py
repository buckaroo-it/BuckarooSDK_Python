


from typing import Dict, Any
from .payment_builder import PaymentBuilder
from .capabilities.bank_transfer_capabilities import BankTransferCapabilities
from ...models.payment_response import PaymentResponse

class BancontactBuilder(PaymentBuilder):
    """Builder for Bancontact payments."""

    def get_service_name(self) -> str:
        """Get the service name for bancontactmrcash payments."""
        return "bancontactmrcash"
    
    def savetoken(self, savetoken: str) -> 'BancontactBuilder':
        """Set the save token."""
        return self.add_parameter("savetoken", savetoken)