from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self
from ..models.payment_request import PaymentRequest, ClientIP, Service, ServiceList, Parameter
from ..models.payment_response import PaymentResponse
from ..services.service_parameter_validator import ServiceParameterValidator
from ..services.transaction_service import TransactionExecutor, ITransactionExecutor
from ..exceptions._parameter_validation_error import ParameterValidationError, RequiredParameterMissingError


class BaseBuilder(ABC):
    """Abstract base class for all builders (payments and solutions)."""

    def __init__(self, client, executor: Optional[ITransactionExecutor] = None):
        """Initialize with client instance.

        Args:
            client: BuckarooClient instance.
            executor: Optional transaction executor. If omitted a ``TransactionExecutor``
                      is created automatically. Pass a mock here in unit tests to avoid
                      real HTTP calls.
        """
        self._client = client
        self._executor: ITransactionExecutor = executor if executor is not None else TransactionExecutor(client)
        self._currency: Optional[str] = None
        self._amount_debit: Optional[float] = None
        self._description: Optional[str] = None
        self._invoice: Optional[str] = None
        self._return_url: Optional[str] = None
        self._return_url_cancel: Optional[str] = None
        self._return_url_error: Optional[str] = None
        self._return_url_reject: Optional[str] = None
        self._continue_on_incomplete: str = "1"
        self._push_url: Optional[str] = None
        self._push_url_failure: Optional[str] = None
        self._client_ip: Optional[ClientIP] = None
        self._service_parameters: List[Parameter] = []
        self._payload: Dict[str, Any] = {}  # Store original payload
        self._validator = ServiceParameterValidator(self)
    
    def currency(self, currency: str) -> Self:
        """Set the currency for the payment."""
        self._currency = currency
        return self
    
    def amount(self, amount: float) -> Self:
        """Set the amount for the payment."""
        self._amount_debit = amount
        return self
    
    def description(self, description: str) -> Self:
        """Set the description for the payment."""
        self._description = description
        return self
    
    def invoice(self, invoice: str) -> Self:
        """Set the invoice number for the payment."""
        self._invoice = invoice
        return self
    
    def return_url(self, url: str) -> Self:
        """Set the return URL for successful payment."""
        self._return_url = url
        return self
    
    def return_url_cancel(self, url: str) -> Self:
        """Set the return URL for cancelled payment."""
        self._return_url_cancel = url
        return self
    
    def return_url_error(self, url: str) -> Self:
        """Set the return URL for payment error."""
        self._return_url_error = url
        return self
    
    def return_url_reject(self, url: str) -> Self:
        """Set the return URL for rejected payment."""
        self._return_url_reject = url
        return self
    
    def continue_on_incomplete(self, continue_incomplete: str) -> Self:
        """Set whether to continue on incomplete payment."""
        self._continue_on_incomplete = continue_incomplete
        return self
    
    def push_url(self, url: str) -> Self:
        """Set the Push (webhook) URL."""
        self._push_url = url
        return self

    def push_url_failure(self, url: str) -> Self:
        """Set the Push URL for failure notifications."""
        self._push_url_failure = url
        return self

    def client_ip(self, ip_address: str, ip_type: int = 0) -> Self:
        """Set the client IP information."""
        self._client_ip = ClientIP(type=ip_type, address=ip_address)
        return self
    
    def add_parameter(self, key: str, value: Any, group_type: Optional[str] = None, group_id: Optional[str] = None) -> Self:
        """Add a custom parameter to the service.

        Args:
            key: Parameter name
            value: Parameter value (will be converted to string unless it's a list/dict)
            group_type: Optional group type for grouped parameters
            group_id: Optional group ID for grouped parameters
        """
        # Handle list of dictionaries (e.g., articles)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    # Each item in the list becomes a group
                    for item_key, item_value in item.items():
                        str_value = (
                            str(item_value).lower()
                            if isinstance(item_value, bool)
                            else str(item_value)
                        )
                        parameter = Parameter(
                            name=item_key.capitalize(),
                            value=str_value,
                            group_type=key.capitalize(),  # e.g., "articles"
                            group_id=str(index + 1),  # 1-based index
                        )
                        self._service_parameters.append(parameter)
            return self

        # Handle regular parameters
        # Convert value to string for API compatibility
        str_value = str(value).lower() if isinstance(value, bool) else str(value)

        parameter = Parameter(
            name=key.capitalize(),
            value=str_value,
            group_type=group_type.capitalize() if group_type else None,
            group_id=group_id,
        )

        self._service_parameters.append(parameter)
        return self

    # Validation convenience methods
    def is_parameter_allowed(self, param_name: str, action: str = "Pay") -> bool:
        """Check if a parameter is allowed for the given action."""
        return self._validator.is_parameter_allowed(param_name, action)

    def get_parameter_info(self, action: str = "Pay") -> Dict[str, Any]:
        """Get information about allowed parameters for an action."""
        return self._validator.get_parameter_info(action)

    def get_normalized_parameter_name(self, param_name: str, action: str = "Pay") -> str:
        """Get the official parameter name that matches the input."""
        return self._validator.get_normalized_parameter_name(param_name, action)

    def _validate_and_filter_service_parameters(
        self, action: str = "Pay", strict: bool = False
    ) -> None:
        """
        Validate and filter service parameters just before building.

        Args:
            action (str): The action being performed
            strict (bool): If True, throws exceptions for missing required parameters.
                          If False, filters invalid parameters and only warns.

        Raises:
            RequiredParameterMissingError: If required parameters are missing (when strict=True)
            ParameterValidationError: If parameters are invalid (when strict=True)
        """
        self._service_parameters = self._validator.validate_all_parameters(
            self._service_parameters, action, strict=strict
        )
    
    def from_dict(self, data: Dict[str, Any]) -> Self:
        """
        Populate the builder from a dictionary of parameters.

        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters

        Returns:
            BaseBuilder: Self for method chaining

        Supported keys:
            - currency: Payment currency (e.g., 'EUR', 'USD')
            - amount: Payment amount (float)
            - description: Payment description (str)
            - invoice: Invoice number (str)
            - return_url: Success return URL (str)
            - return_url_cancel: Cancel return URL (str)
            - return_url_error: Error return URL (str)
            - return_url_reject: Reject return URL (str)
            - continue_on_incomplete: Continue on incomplete flag (str)
            - client_ip: Client IP address (str or dict with 'address' and 'type')
            - service_parameters: Additional service-specific parameters (dict)
        """
        # Map dictionary keys to builder methods
        if "currency" in data:
            self.currency(data["currency"])

        if "amount" in data:
            self.amount(data["amount"])

        if "description" in data:
            self.description(data["description"])

        if "invoice" in data:
            self.invoice(data["invoice"])

        if "return_url" in data:
            self.return_url(data["return_url"])

        if "return_url_cancel" in data:
            self.return_url_cancel(data["return_url_cancel"])

        if "return_url_error" in data:
            self.return_url_error(data["return_url_error"])

        if "return_url_reject" in data:
            self.return_url_reject(data["return_url_reject"])

        if "continue_on_incomplete" in data:
            self.continue_on_incomplete(data["continue_on_incomplete"])

        if "push_url" in data:
            self.push_url(data["push_url"])
        if "push_url_failure" in data:
            self.push_url_failure(data["push_url_failure"])

        if "client_ip" in data:
            client_ip_data = data["client_ip"]
            if isinstance(client_ip_data, str):
                self.client_ip(client_ip_data)
            elif isinstance(client_ip_data, dict):
                address = client_ip_data.get("address", "0.0.0.0")
                ip_type = client_ip_data.get("type", 0)
                self.client_ip(address, ip_type)

        if "service_parameters" in data:
            service_params = data["service_parameters"]

            for key, value in service_params.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        self.add_parameter(sub_key, sub_value, key)
                else:
                    self.add_parameter(key, value)

        # Store the original payload for later use
        self._payload = data.copy()

        return self

    @abstractmethod
    def get_service_name(self) -> str:
        """Get the service name for this payment method."""
        raise NotImplementedError

    @abstractmethod
    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        """
        Get the allowed service parameters for this payment method and action.

        Args:
            action (str): The action being performed (Pay, Authorize, Refund, etc.)

        Returns:
            Dict[str, Any]: Dictionary where keys are parameter names and values are
                          parameter metadata (type, required, etc.)
        """
        raise NotImplementedError

    def required_fields(self, action: str = "Pay") -> Dict[str, Any]:
        """
        Get the required fields for this payment method and action.
        Can be overridden by specific payment builders to customize required fields based on action.

        Args:
            action (str): The action being performed (Pay, Authorize, Refund, Capture, etc.)

        Returns:
            Dict[str, Any]: Dictionary mapping field names to their current values
        """
        return {
            "currency": self._currency,
            "amount_debit": self._amount_debit,
            "description": self._description,
            "invoice": self._invoice,
            "return_url": self._return_url,
            "return_url_cancel": self._return_url_cancel,
            "return_url_error": self._return_url_error,
            "return_url_reject": self._return_url_reject,
        }

    def _validate_required_fields(self, action: str = "Pay") -> None:
        """Validate that all required fields are set.

        Args:
            action (str): The action being performed (Pay, Authorize, Refund, Capture, etc.)
        """
        missing_fields = [field for field, value in self.required_fields(action).items() if value is None]
        if len(missing_fields) == 1:
            raise RequiredParameterMissingError(missing_fields[0], action=action)
        elif missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
    
    def build(self, action: str = "Pay", validate: bool = True, strict_validation: bool = False) -> PaymentRequest:
        """Build the payment request.

        Args:
            action (str): The action to perform (Pay, Authorize, Refund, etc.)
            validate (bool): Whether to validate and filter service parameters
            strict_validation (bool): If True, throws exceptions for missing required parameters.
                                    If False, filters invalid parameters and only warns.

        Raises:
            ValueError: If required payment fields are missing
            RequiredParameterMissingError: If required service parameters are missing (when strict_validation=True)
            ParameterValidationError: If service parameters are invalid (when strict_validation=True)
        """
        self._validate_required_fields(action)

        # Validate and filter service parameters if enabled
        if validate:
            self._validate_and_filter_service_parameters(action, strict=strict_validation)

        # Create service with parameters
        service = Service(
            name=self.get_service_name(),
            action=action,
            parameters=self._service_parameters if self._service_parameters else None,
        )

        # Create service list
        service_list = ServiceList(services=[service])

        # Build payment request
        payment_request = PaymentRequest(
            currency=self._currency,
            amount_debit=self._amount_debit,
            description=self._description,
            invoice=self._invoice,
            return_url=self._return_url,
            return_url_cancel=self._return_url_cancel,
            return_url_error=self._return_url_error,
            return_url_reject=self._return_url_reject,
            continue_on_incomplete=self._continue_on_incomplete,
            push_url=self._push_url,
            push_url_failure=self._push_url_failure,
            client_ip=self._client_ip,
            services=service_list,
        )

        return payment_request

    def _post_data_request(self, request_data: Dict[str, Any]) -> PaymentResponse:
        """Post a data request to the Buckaroo API."""
        return self._executor.post_data_request(request_data)

    def _post_transaction(self, request_data: Dict[str, Any]) -> PaymentResponse:
        """Post a transaction to the Buckaroo API."""
        return self._executor.post_transaction(request_data)
