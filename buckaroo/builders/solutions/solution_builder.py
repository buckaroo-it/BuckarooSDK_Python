from typing import Dict, Any
from ..base_builder import BaseBuilder


class SolutionBuilder(BaseBuilder):
    """Abstract base class for solution builders."""
    
    def required_fields(self, action: str = "Pay") -> Dict[str, Any]:
        """
        Override to return empty dict as solutions typically have no required fields.
        
        Args:
            action (str): The action being performed
        
        Returns:
            Dict[str, Any]: Empty dictionary (no required fields for solutions)
        """
        return {}