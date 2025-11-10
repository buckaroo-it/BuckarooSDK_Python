


from typing import Dict, Any
from .payment_builder import PaymentBuilder

class GiftcardsBuilder(PaymentBuilder):
    """Builder for Giftcards payments."""

    def get_service_name(self) -> str:
        """Get the service name for Giftcards payments."""
        return self._payload.get('giftcard_name', 'Giftcards')
    
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """Get the allowed service parameters for Giftcards payments based on action."""

        if action.lower() in ["pay"]:
            if self._payload.get('giftcard_name').lower() == 'fashioncheque':
                return {
                    "FashionChequeCardNumber": {"type": str, "required": True, "description": "Save payment token for future use"},
                    "FashionChequePIN": {"type": str, "required": True, "description": "Save payment token for future use"},
                }
            
            if self._payload.get('giftcard_name').lower() == 'intersolve':
                return {
                    "IntersolveCardnumber": {"type": str, "required": True, "description": ""},
                    "IntersolvePIN": {"type": str, "required": True, "description": ""},
                }
            
            if self._payload.get('giftcard_name').lower() == 'tcs':
                return {
                    "TCSCardnumber": {"type": str, "required": True, "description": ""},
                    "TCSValidationCode": {"type": str, "required": True, "description": ""},
                }
            
            return {
                "Cardnumber": {"type": str, "required": True, "description": ""},
                "PIN": {"type": str, "required": True, "description": ""},
                "LastName": {"type": str, "required": False, "description": ""},
                "Email": {"type": str, "required": False, "description": ""},
            }

        
        return {}
