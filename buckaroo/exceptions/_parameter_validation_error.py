"""
Exception for parameter validation errors.
"""

from typing import Optional
from ._buckaroo_error import BuckarooError


class ParameterValidationError(BuckarooError):
    """Exception raised when parameter validation fails."""

    def __init__(
        self,
        message: str,
        parameter_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        action: Optional[str] = None,
        service_name: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.parameter_name = parameter_name
        self.expected_type = expected_type
        self.action = action
        self.service_name = service_name


class RequiredParameterMissingError(ParameterValidationError):
    """Exception raised when a required parameter is missing."""

    def __init__(
        self,
        parameter_name: str,
        action: Optional[str] = None,
        service_name: Optional[str] = None,
        **kwargs,
    ):
        service_info = f" for {service_name}" if service_name else ""
        action_info = f" {action} action" if action else ""
        message = f"Required parameter '{parameter_name}' is missing{service_info}{action_info}"
        super().__init__(
            message=message,
            parameter_name=parameter_name,
            action=action,
            service_name=service_name,
            **kwargs,
        )