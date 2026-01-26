from typing import Dict, Any

from buckaroo.models.payment_response import PaymentResponse
from .payment_builder import PaymentBuilder

class KlarnaKPBuilder(PaymentBuilder):
    """Builder for Klarna KP payments with bank transfer capabilities."""

    def required_fields(self, action: str = "Pay") -> Dict[str, Any]:
        """
        Get the required fields for this payment method and action.
        Can be overridden by specific payment builders to customize required fields.
        
        Args:
            action (str): The action being performed (Pay, Reserve, etc.)
        
        Returns:
            Dict[str, Any]: Dictionary mapping field names to their current values
        """
        if action.lower() == "reserve":
            return {
                'currency': self._currency,
                'invoice': self._invoice,
            }
        
        return {
        }

    def get_service_name(self) -> str:
        """Get the service name for Klarna KP payments."""
        return "klarnakp"
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Klarna KP payments based on action."""
        
        if action.lower() in ["pay", "cancelreservation"]:
            return {
                "reservationNumber": {"type": str, "required": True, "description": "Klarna KP reservation number"},
            }
        
        if action.lower() == "reserve":
            return {
                # "reservationNumber": {"type": str, "required": True, "description": "Klarna KP reservation number"},
                # "billingCustomer": {"type": list, "required": True, "description": "Billing customer information"},
                # "shippingCustomer": {"type": list, "required": True, "description": "Shipping customer information"},
                "operatingCountry": {"type": str, "required": True, "description": "Operating country code"},
                "article": {"type": list, "required": True, "description": "Klarna KP articles"},
            }

        if action.lower() in ["pay", "cancelreservation", "extendreservation"]:
            return {
                "reservationNumber": {"type": str, "required": True, "description": "Klarna KP reservation number"},
            }
        
        if action.lower() == "updatereservation":
            return {
                "reservationNumber": {"type": str, "required": True, "description": "Klarna KP reservation number"},
                "article": {"type": list, "required": True, "description": "Klarna KP articles"},
            }
        
        if action.lower() == "addshippinginfo":
            return {
                "originalTransactionKey": {"type": str, "required": True, "description": "Original transaction key"},
                "shippingMethod": {"type": str, "required": False, "description": "Shipping method"},
                "company": {"type": str, "required": False, "description": "Shipping company name"},
                "trackingNumber": {"type": str, "required": False, "description": "Shipping tracking number"}
            }
        
        return {}
    
    def reserve(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        
        payment_request = self.build("Reserve", validate=validate)
        request_data = payment_request.to_dict()
        
        return self._post_data_request(request_data)
    
    def cancelReservation(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        
        payment_request = self.build("CancelReservation", validate=validate)
        request_data = payment_request.to_dict()
        
        return self._post_data_request(request_data)
    
    def updateReservation(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        
        payment_request = self.build("UpdateReservation", validate=validate)
        request_data = payment_request.to_dict()
        
        return self._post_data_request(request_data)
    
    def extendReservation(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        
        payment_request = self.build("ExtendReservation", validate=validate)
        request_data = payment_request.to_dict()
        
        return self._post_data_request(request_data)
    
    def addShippingInfo(self: 'PaymentBuilder', validate: bool = True) -> PaymentResponse:
        
        payment_request = self.build("AddShippingInfo", validate=validate)
        request_data = payment_request.to_dict()
        
        return self._post_data_request(request_data)