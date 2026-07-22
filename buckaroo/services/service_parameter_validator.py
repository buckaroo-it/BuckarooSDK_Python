"""
Service parameter validation for payment builders.
"""

import logging
from typing import Any, Dict, List
from buckaroo.models.payment_request import Parameter
from buckaroo.exceptions._parameter_validation_error import (
    ParameterValidationError,
    RequiredParameterMissingError,
)


class ServiceParameterValidator:
    """Handles validation and filtering of service parameters for payment methods."""

    def __init__(self, builder) -> None:
        """
        Args:
            builder: A builder object that exposes ``get_allowed_service_parameters(action)``
                     and ``get_service_name()`` methods.
        """
        self._get_allowed_params = builder.get_allowed_service_parameters
        self._get_service_name = builder.get_service_name

    def normalize_parameter_name(self, param_name: str) -> str:
        """Normalize parameter name to lowercase and remove underscores for matching.

        Also extracts the actual parameter name from dot notation like 'service_parameters.issuer' -> 'issuer'
        """
        # Extract parameter name from dot notation (e.g., 'service_parameters.issuer' -> 'issuer')
        if "." in param_name:
            param_name = param_name.split(".")[-1]
        return param_name.lower().replace("_", "")

    def validate_parameter_type(self, key: str, value: Any, param_config: Dict[str, Any]) -> None:
        """
        Validate parameter value against expected type.

        Args:
            key (str): Parameter name
            value (Any): Parameter value
            param_config (Dict[str, Any]): Parameter configuration with type info

        Raises:
            ParameterValidationError: If parameter type is invalid
        """
        if "type" not in param_config:
            return

        expected_type = param_config["type"]

        # Skip validation for grouped parameters (they're already expanded)
        # Grouped parameters will have their structure validated before expansion
        if expected_type in (list, dict):
            return

        # Handle tuple of types (e.g., (str, bool))
        if isinstance(expected_type, tuple):
            type_valid = any(isinstance(value, t) for t in expected_type)
            if not type_valid:
                # Allow string representations of booleans for bool types
                if bool in expected_type and isinstance(value, str):
                    if value.lower() not in ["true", "false"]:
                        type_names = [t.__name__ for t in expected_type]
                        raise ParameterValidationError(
                            f"Parameter '{key}' must be one of types {type_names} or 'true'/'false' string",
                            parameter_name=key,
                            expected_type=str(type_names),
                            service_name=self._get_service_name(),
                        )
                else:
                    type_names = [t.__name__ for t in expected_type]
                    raise ParameterValidationError(
                        f"Parameter '{key}' must be one of types {type_names}, got {type(value).__name__}",
                        parameter_name=key,
                        expected_type=str(type_names),
                        service_name=self._get_service_name(),
                    )
        else:
            if not isinstance(value, expected_type):
                # Allow string representations of booleans
                if expected_type is bool and isinstance(value, str):
                    if value.lower() not in ["true", "false"]:
                        raise ParameterValidationError(
                            f"Parameter '{key}' must be a boolean or 'true'/'false' string",
                            parameter_name=key,
                            expected_type=expected_type.__name__,
                            service_name=self._get_service_name(),
                        )
                else:
                    raise ParameterValidationError(
                        f"Parameter '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}",
                        parameter_name=key,
                        expected_type=expected_type.__name__,
                        service_name=self._get_service_name(),
                    )

    def validate_single_parameter(self, key: str, value: Any, action: str = "Pay") -> None:
        """
        Validate a single service parameter against allowed parameters for the specified action.

        Args:
            key (str): Parameter name
            value (Any): Parameter value
            action (str): The action being performed

        Raises:
            ParameterValidationError: If parameter is not allowed or invalid
        """
        allowed_params = self._get_allowed_params(action)

        if key not in allowed_params:
            raise ParameterValidationError(
                f"Parameter '{key}' is not allowed for {self._get_service_name()} {action} action. "
                f"Allowed parameters: {list(allowed_params.keys())}",
                parameter_name=key,
                action=action,
                service_name=self._get_service_name(),
            )

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
        if value.lower() in ["true", "false"]:
            return value.lower() == "true"
        return value

    def validate_required_parameters(
        self, parameters: List[Parameter], action: str = "Pay"
    ) -> None:
        """
        Validate that all required parameters are provided.

        Args:
            parameters (List[Parameter]): List of provided parameters
            action (str): The action being performed

        Raises:
            RequiredParameterMissingError: If any required parameter is missing
        """
        allowed_params = self._get_allowed_params(action)

        # Create a normalized lookup for provided parameters
        # Include both regular parameters and group_types
        provided_params = {}
        for param in parameters:
            # Add the parameter name
            normalized_name = self.normalize_parameter_name(param.name)
            provided_params[normalized_name] = param.name

            # Also add the group_type if it exists
            if param.group_type:
                normalized_group = self.normalize_parameter_name(param.group_type)
                provided_params[normalized_group] = param.group_type

        # Check each allowed parameter to see if it's required and provided
        missing_required = []
        for param_name, param_config in allowed_params.items():
            if param_config.get("required", False):
                # For dot notation keys (e.g., 'service_parameters.issuer'), extract the actual param name
                normalized_param = self.normalize_parameter_name(param_name)
                if normalized_param not in provided_params:
                    # Use just the parameter name (not full dot notation) in error message
                    missing_required.append(
                        param_name.split(".")[-1] if "." in param_name else param_name
                    )

        # Throw exception if any required parameters are missing
        if missing_required:
            if len(missing_required) == 1:
                raise RequiredParameterMissingError(
                    parameter_name=missing_required[0],
                    action=action,
                    service_name=self._get_service_name(),
                )
            else:
                # Multiple missing parameters
                raise ParameterValidationError(
                    f"Required parameters missing for {self._get_service_name()} {action} action: {', '.join(missing_required)}",
                    action=action,
                    service_name=self._get_service_name(),
                )

    def validate_and_filter_parameters(
        self, parameters: List[Parameter], action: str = "Pay"
    ) -> List[Parameter]:
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

        allowed_params = self._get_allowed_params(action)

        # Create normalized lookup for allowed parameters
        normalized_allowed = {
            self.normalize_parameter_name(key): key for key in allowed_params.keys()
        }

        valid_parameters = []
        invalid_params = []

        for param in parameters:
            # For grouped parameters (like articles), validate the group_type instead of the parameter name
            if param.group_type and param.group_type != "__from_service_params__":
                normalized_group_type = self.normalize_parameter_name(param.group_type)
                if normalized_group_type in normalized_allowed:
                    # Grouped parameter is valid - no need to validate individual fields
                    valid_parameters.append(param)
                else:
                    invalid_params.append(
                        f"{param.name} (group: {param.group_type}): group not allowed for {self._get_service_name()} {action} action"
                    )
            else:
                # Regular parameter - validate including source check
                normalized_param_name = self.normalize_parameter_name(param.name)
                is_from_service_params = param.group_type == "__from_service_params__"

                if normalized_param_name in normalized_allowed:
                    try:
                        # Use the original allowed parameter name for validation
                        allowed_param_name = normalized_allowed[normalized_param_name]

                        # Check if source matches requirement
                        requires_service_params = allowed_param_name.startswith(
                            "service_parameters."
                        )
                        if requires_service_params and not is_from_service_params:
                            invalid_params.append(
                                f"{param.name}: must be in service_parameters dict"
                            )
                            continue
                        elif not requires_service_params and is_from_service_params:
                            invalid_params.append(
                                f"{param.name}: should be at top-level, not in service_parameters"
                            )
                            continue

                        # Convert parameter value for validation
                        param_value = self.normalize_parameter_value(param.value)

                        self.validate_single_parameter(allowed_param_name, param_value, action)
                        valid_parameters.append(param)
                    except ParameterValidationError as e:
                        invalid_params.append(f"{param.name}: {str(e)}")
                else:
                    invalid_params.append(
                        f"{param.name}: not allowed for {self._get_service_name()} {action} action"
                    )

        if invalid_params:
            logging.warning(
                "Filtered out invalid service parameters for %s action: %s", action, invalid_params
            )

        return valid_parameters

    def validate_all_parameters(
        self, parameters: List[Parameter], action: str = "Pay", strict: bool = True
    ) -> List[Parameter]:
        """
        Validate all service parameters including required parameter checks.

        Args:
            parameters (List[Parameter]): List of parameters to validate
            action (str): The action being performed
            strict (bool): If True, throws exceptions for validation errors. If False, filters invalid parameters.

        Returns:
            List[Parameter]: Validated parameters (if strict=False, invalid ones are filtered out)

        Raises:
            RequiredParameterMissingError: If required parameters are missing (when strict=True)
            ParameterValidationError: If parameters are invalid (when strict=True)
        """
        if strict:
            # First validate that all required parameters are present
            self.validate_required_parameters(parameters, action)

            # Then validate each parameter individually - strict mode throws exceptions
            for param in parameters:
                normalized_param_name = self.normalize_parameter_name(param.name)
                allowed_params = self._get_allowed_params(action)
                normalized_allowed = {
                    self.normalize_parameter_name(key): key for key in allowed_params.keys()
                }

                if normalized_param_name in normalized_allowed:
                    allowed_param_name = normalized_allowed[normalized_param_name]
                    param_value = self.normalize_parameter_value(param.value)
                    self.validate_single_parameter(allowed_param_name, param_value, action)
                else:
                    raise ParameterValidationError(
                        f"Parameter '{param.name}' is not allowed for {self._get_service_name()} {action} action",
                        parameter_name=param.name,
                        action=action,
                        service_name=self._get_service_name(),
                    )

            return parameters
        else:
            # Non-strict mode: just filter out invalid parameters and check required ones at the end
            valid_parameters = self.validate_and_filter_parameters(parameters, action)
            self.validate_required_parameters(valid_parameters, action)
            return valid_parameters

    def get_parameter_info(self, action: str = "Pay") -> Dict[str, Any]:
        """
        Get information about allowed parameters for an action.

        Args:
            action (str): The action to get parameter info for

        Returns:
            Dict[str, Any]: Parameter information including types and requirements
        """
        return self._get_allowed_params(action)

    def is_parameter_allowed(self, param_name: str, action: str = "Pay") -> bool:
        """
        Check if a parameter is allowed for the given action.

        Args:
            param_name (str): Parameter name to check
            action (str): The action being performed

        Returns:
            bool: True if parameter is allowed, False otherwise
        """
        allowed_params = self._get_allowed_params(action)
        normalized_allowed = {
            self.normalize_parameter_name(key): key for key in allowed_params.keys()
        }
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
        allowed_params = self._get_allowed_params(action)
        normalized_allowed = {
            self.normalize_parameter_name(key): key for key in allowed_params.keys()
        }
        normalized_param = self.normalize_parameter_name(param_name)

        return normalized_allowed.get(normalized_param, "")
