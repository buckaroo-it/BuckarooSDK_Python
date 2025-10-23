"""
Service parameter validation for payment builders.
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod
from ...models.payment_request import Parameter


class ServiceParameterValidator:
    """Handles validation and filtering of service parameters for payment methods."""
    
    def __init__(self, payment_builder):
        """
        Initialize validator with payment builder reference.
        
        Args:
            payment_builder: The payment builder instance to validate for
        """
        self.payment_builder = payment_builder
    
    def normalize_parameter_name(self, param_name: str) -> str:
        """Normalize parameter name to lowercase and remove underscores for matching."""
        return param_name.lower().replace('_', '')
    
    def validate_parameter_type(self, key: str, value: Any, param_config: Dict[str, Any]) -> None:
        """
        Validate parameter value against expected type.
        
        Args:
            key (str): Parameter name
            value (Any): Parameter value
            param_config (Dict[str, Any]): Parameter configuration with type info
            
        Raises:
            ValueError: If parameter type is invalid
        """
        if 'type' not in param_config:
            return
            
        expected_type = param_config['type']
        
        # Handle tuple of types (e.g., (str, bool))
        if isinstance(expected_type, tuple):
            type_valid = any(isinstance(value, t) for t in expected_type)
            if not type_valid:
                # Allow string representations of booleans for bool types
                if bool in expected_type and isinstance(value, str):
                    if value.lower() not in ['true', 'false']:
                        type_names = [t.__name__ for t in expected_type]
                        raise ValueError(f"Parameter '{key}' must be one of types {type_names} or 'true'/'false' string")
                else:
                    type_names = [t.__name__ for t in expected_type]
                    raise ValueError(f"Parameter '{key}' must be one of types {type_names}, got {type(value).__name__}")
        else:
            if not isinstance(value, expected_type):
                # Allow string representations of booleans
                if expected_type == bool and isinstance(value, str):
                    if value.lower() not in ['true', 'false']:
                        raise ValueError(f"Parameter '{key}' must be a boolean or 'true'/'false' string")
                else:
                    raise ValueError(f"Parameter '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}")
    
    def validate_single_parameter(self, key: str, value: Any, action: str = "Pay") -> None:
        """
        Validate a single service parameter against allowed parameters for the specified action.
        
        Args:
            key (str): Parameter name
            value (Any): Parameter value
            action (str): The action being performed
            
        Raises:
            ValueError: If parameter is not allowed or invalid
        """
        allowed_params = self.payment_builder.get_allowed_service_parameters(action)
        
        if key not in allowed_params:
            raise ValueError(f"Parameter '{key}' is not allowed for {self.payment_builder.get_service_name()} {action} action. "
                           f"Allowed parameters: {list(allowed_params.keys())}")
        
        param_config = allowed_params[key]
        self.validate_parameter_type(key, value, param_config)
    
    def normalize_parameter_value(self, value: str) -> Any:
        """
        Convert parameter value back to appropriate type for validation.
        
        Args:
            value (str): String parameter value
            
        Returns:
            Any: Converted value (bool for 'true'/'false', otherwise string)
        """
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        return value
    
    def validate_and_filter_parameters(self, parameters: List[Parameter], action: str = "Pay") -> List[Parameter]:
        """
        Validate and filter service parameters, removing invalid ones.
        
        Args:
            parameters (List[Parameter]): List of parameters to validate
            action (str): The action being performed
            
        Returns:
            List[Parameter]: Filtered list with only valid parameters
        """
        if not parameters:
            return []
            
        allowed_params = self.payment_builder.get_allowed_service_parameters(action)
        # Create normalized lookup for allowed parameters
        normalized_allowed = {self.normalize_parameter_name(key): key for key in allowed_params.keys()}
        
        valid_parameters = []
        invalid_params = []
        
        for param in parameters:
            normalized_param_name = self.normalize_parameter_name(param.name)
            
            if normalized_param_name in normalized_allowed:
                try:
                    # Use the original allowed parameter name for validation
                    allowed_param_name = normalized_allowed[normalized_param_name]
                    
                    # Convert parameter value for validation
                    param_value = self.normalize_parameter_value(param.value)
                    
                    self.validate_single_parameter(allowed_param_name, param_value, action)
                    valid_parameters.append(param)
                except ValueError as e:
                    invalid_params.append(f"{param.name}: {str(e)}")
            else:
                invalid_params.append(f"{param.name}: not allowed for {self.payment_builder.get_service_name()} {action} action")
        
        if invalid_params:
            print(f"Warning: Filtered out invalid service parameters for {action} action: {invalid_params}")
        
        return valid_parameters
    
    def get_parameter_info(self, action: str = "Pay") -> Dict[str, Any]:
        """
        Get information about allowed parameters for an action.
        
        Args:
            action (str): The action to get parameter info for
            
        Returns:
            Dict[str, Any]: Parameter information including types and requirements
        """
        return self.payment_builder.get_allowed_service_parameters(action)
    
    def is_parameter_allowed(self, param_name: str, action: str = "Pay") -> bool:
        """
        Check if a parameter is allowed for the given action.
        
        Args:
            param_name (str): Parameter name to check
            action (str): The action being performed
            
        Returns:
            bool: True if parameter is allowed, False otherwise
        """
        allowed_params = self.payment_builder.get_allowed_service_parameters(action)
        normalized_allowed = {self.normalize_parameter_name(key): key for key in allowed_params.keys()}
        normalized_param = self.normalize_parameter_name(param_name)
        
        return normalized_param in normalized_allowed
    
    def get_normalized_parameter_name(self, param_name: str, action: str = "Pay") -> str:
        """
        Get the official parameter name that matches the input (after normalization).
        
        Args:
            param_name (str): Input parameter name
            action (str): The action being performed
            
        Returns:
            str: Official parameter name, or empty string if not found
        """
        allowed_params = self.payment_builder.get_allowed_service_parameters(action)
        normalized_allowed = {self.normalize_parameter_name(key): key for key in allowed_params.keys()}
        normalized_param = self.normalize_parameter_name(param_name)
        
        return normalized_allowed.get(normalized_param, "")