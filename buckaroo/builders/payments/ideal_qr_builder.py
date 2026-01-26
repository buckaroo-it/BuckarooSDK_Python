from typing import Dict, Any
from .payment_builder import PaymentBuilder

class IdealQrBuilder(PaymentBuilder):
    """Builder for iDEAL QR payments with bank transfer capabilities."""
    
    @property
    def required_fields(self) -> Dict[str, Any]:
        """
        Get the required fields for this payment method.
        Can be overridden by specific payment builders to customize required fields.
        
        Returns:
            Dict[str, Any]: Dictionary mapping field names to their current values
        """
        return {
            'currency': self._currency,
            'description': self._description,
            'invoice': self._invoice,
            'return_url': self._return_url,
            'return_url_cancel': self._return_url_cancel,
            'return_url_error': self._return_url_error,
            'return_url_reject': self._return_url_reject,
        }
    
    def get_service_name(self) -> str:
        """Get the service name for iDEAL QR payments."""
        return "IdealQr"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for iDEAL QR payments based on action."""
        
        if action.lower() in ["generate"]:
            return {
                "amount": {"type": str, "required": True, "description": "iDEAL QR payment amount"},
                "amountIsChangeable": {"type": bool, "required": True, "description": "Indicates if the amount can be changed"},
                "purchaseId": {"type": str, "required": True, "description": "Unique purchase identifier"},
                "description": {"type": str, "required": True, "description": "Description of the payment"},
                "isOneOff": {"type": bool, "required": True, "description": "Indicates if the payment is a one-off"},
                "expiration": {"type": str, "required": True, "description": "Expiration time for the QR code"},
                "imageSize": {"type": str, "required": True, "description": "Size of the QR code image"},
                "isProcessing": {"type": bool, "required": False, "description": "Indicates if the payment is processing"},
                "minAmount": {"type": str, "required": False, "description": "Minimum amount allowed for the payment"},
                "maxAmount": {"type": str, "required": False, "description": "Maximum amount allowed for the payment"},
            }

        return {}
    
    def generate(self, validate: bool = True, strict_validation: bool = False) -> PaymentResponse:
        # Build the payment request
        payment_request = self.build("Generate", validate=validate, strict_validation=strict_validation)
        
        # Convert to dictionary for API
        request_data = payment_request.to_dict()

        return self._post_data_request(request_data)