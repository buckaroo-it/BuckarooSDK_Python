"""
Exception for parameter validation errors.
"""

from ._buckaroo_error import BuckarooError


class ParameterValidationError(BuckarooError):
    """Exception raised when parameter validation fails."""
    
    def __init__(self, message: str, parameter_name: str = None, expected_type: str = None, 
                 action: str = None, service_name: str = None):
        """
        Initialize parameter validation error.
        
        Args:
            message (str): Error message
            parameter_name (str, optional): Name of the parameter that failed validation
            expected_type (str, optional): Expected parameter type
            action (str, optional): Action being performed when validation failed
            service_name (str, optional): Service name where validation failed
        """
        super().__init__(message)
        self.parameter_name = parameter_name
        self.expected_type = expected_type
        self.action = action
        self.service_name = service_name
        self._message = message
    
    def __str__(self):
        """Return string representation of the error."""
        return self._message


class RequiredParameterMissingError(ParameterValidationError):
    """Exception raised when a required parameter is missing."""
    
    def __init__(self, parameter_name: str, action: str = None, service_name: str = None):
        """
        Initialize required parameter missing error.
        
        Args:
            parameter_name (str): Name of the missing required parameter
            action (str, optional): Action being performed
            service_name (str, optional): Service name
        """
        parts = [p for p in (service_name, f"{action} action" if action else None) if p]
        qualifier = f" for {' '.join(parts)}" if parts else ""
        message = f"Required parameter '{parameter_name}' is missing{qualifier}"
        
        super().__init__(
            message=message,
            parameter_name=parameter_name,
            action=action,
            service_name=service_name
        )