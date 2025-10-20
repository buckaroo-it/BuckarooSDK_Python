from typing import Dict, Any
from .payment_builder import PaymentBuilder


class IdealBuilder(PaymentBuilder):
    """Builder for iDEAL payments."""
    
    def get_service_name(self) -> str:
        """Get the service name for iDEAL payments."""
        return "ideal"
    
    def issuer(self, issuer: str) -> 'IdealBuilder':
        """Set the iDEAL issuer."""
        return self.add_parameter("issuer", issuer)
    
    def from_dict(self, data: Dict[str, Any]) -> 'IdealBuilder':
        """
        Populate the iDEAL builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
        Returns:
            IdealBuilder: Self for method chaining
            
        Additional iDEAL-specific keys:
            - issuer: iDEAL bank issuer code (str)
        """
        # Call parent from_dict first
        super().from_dict(data)
        
        # Handle iDEAL-specific parameters

        if 'issuer' in data:
            self.issuer(data['issuer'])
            
        return self