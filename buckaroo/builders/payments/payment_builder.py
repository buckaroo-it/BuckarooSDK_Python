from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from ...models.payment_request import PaymentRequest, ClientIP, Service, ServiceList, Parameter
from ...models.payment_response import PaymentResponse
from ...http.client import BuckarooApiError
from .service_parameter_validator import ServiceParameterValidator


class PaymentBuilder(ABC):
    """Abstract base class for payment builders."""
    
    def __init__(self, client):
        """Initialize with client instance."""
        self._client = client
        self._currency: Optional[str] = None
        self._amount_debit: Optional[float] = None
        self._description: Optional[str] = None
        self._invoice: Optional[str] = None
        self._return_url: Optional[str] = None
        self._return_url_cancel: Optional[str] = None
        self._return_url_error: Optional[str] = None
        self._return_url_reject: Optional[str] = None
        self._continue_on_incomplete: str = "1"
        self._client_ip: Optional[ClientIP] = None
        self._service_parameters: List[Parameter] = []
        self._payload: Dict[str, Any] = {}  # Store original payload
        self._validator = ServiceParameterValidator(self)
    
    def currency(self, currency: str) -> 'PaymentBuilder':
        """Set the currency for the payment."""
        self._currency = currency
        return self
    
    def amount(self, amount: float) -> 'PaymentBuilder':
        """Set the amount for the payment."""
        self._amount_debit = amount
        return self
    
    def description(self, description: str) -> 'PaymentBuilder':
        """Set the description for the payment."""
        self._description = description
        return self
    
    def invoice(self, invoice: str) -> 'PaymentBuilder':
        """Set the invoice number for the payment."""
        self._invoice = invoice
        return self
    
    def return_url(self, url: str) -> 'PaymentBuilder':
        """Set the return URL for successful payment."""
        self._return_url = url
        return self
    
    def return_url_cancel(self, url: str) -> 'PaymentBuilder':
        """Set the return URL for cancelled payment."""
        self._return_url_cancel = url
        return self
    
    def return_url_error(self, url: str) -> 'PaymentBuilder':
        """Set the return URL for payment error."""
        self._return_url_error = url
        return self
    
    def return_url_reject(self, url: str) -> 'PaymentBuilder':
        """Set the return URL for rejected payment."""
        self._return_url_reject = url
        return self
    
    def continue_on_incomplete(self, continue_incomplete: str) -> 'PaymentBuilder':
        """Set whether to continue on incomplete payment."""
        self._continue_on_incomplete = continue_incomplete
        return self
    
    def client_ip(self, ip_address: str, ip_type: int = 0) -> 'PaymentBuilder':
        """Set the client IP information."""
        self._client_ip = ClientIP(type=ip_type, address=ip_address)
        return self
    
    def add_parameter(self, key: str, value: Any) -> 'PaymentBuilder':
        """Add a custom parameter to the service."""
        # Convert value to string for API compatibility
        str_value = str(value).lower() if isinstance(value, bool) else str(value)

        parameter = Parameter(name=key, value=str_value)
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
    
    def _validate_and_filter_service_parameters(self, action: str = "Pay") -> None:
        """
        Validate and filter service parameters just before building, removing invalid ones.
        
        Args:
            action (str): The action being performed
        """
        self._service_parameters = self._validator.validate_and_filter_parameters(
            self._service_parameters, action
        )
    
    def from_dict(self, data: Dict[str, Any]) -> 'PaymentBuilder':
        """
        Populate the builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            action (str): The action being performed (Pay, Authorize, Refund, etc.)
            
        Returns:
            PaymentBuilder: Self for method chaining
            
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
        if 'currency' in data:
            self.currency(data['currency'])
            
        if 'amount' in data:
            self.amount(data['amount'])
            
        if 'description' in data:
            self.description(data['description'])
            
        if 'invoice' in data:
            self.invoice(data['invoice'])
            
        if 'return_url' in data:
            self.return_url(data['return_url'])
            
        if 'return_url_cancel' in data:
            self.return_url_cancel(data['return_url_cancel'])
            
        if 'return_url_error' in data:
            self.return_url_error(data['return_url_error'])
            
        if 'return_url_reject' in data:
            self.return_url_reject(data['return_url_reject'])
            
        if 'continue_on_incomplete' in data:
            self.continue_on_incomplete(data['continue_on_incomplete'])
            
        if 'client_ip' in data:
            client_ip_data = data['client_ip']
            if isinstance(client_ip_data, str):
                self.client_ip(client_ip_data)
            elif isinstance(client_ip_data, dict):
                address = client_ip_data.get('address', '0.0.0.0')
                ip_type = client_ip_data.get('type', 0)
                self.client_ip(address, ip_type)
                
        if 'service_parameters' in data:
            service_params = data['service_parameters']
            if isinstance(service_params, dict):
                # Add parameters without validation (validation happens at build time)
                for key, value in service_params.items():
                    self.add_parameter(key, value)

        # Store the original payload for later use
        self._payload = data.copy()
        
        return self
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get the service name for this payment method."""
        pass
    
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
        pass
    
    def _validate_required_fields(self) -> None:
        """Validate that all required fields are set."""
        required_fields = {
            'currency': self._currency,
            'amount_debit': self._amount_debit,
            'description': self._description,
            'invoice': self._invoice,
            'return_url': self._return_url,
            'return_url_cancel': self._return_url_cancel,
            'return_url_error': self._return_url_error,
            'return_url_reject': self._return_url_reject,
        }
        
        missing_fields = [field for field, value in required_fields.items() if value is None]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def build(self, action: str = "Pay", validate: bool = True) -> PaymentRequest:
        """Build the payment request.
        
        Args:
            action (str): The action to perform (Pay, Authorize, Refund, etc.)
            validate (bool): Whether to validate and filter service parameters
        """
        self._validate_required_fields()
        
        # Validate and filter service parameters if enabled
        if validate:
            self._validate_and_filter_service_parameters(action)
        
        # Create service with parameters
        service = Service(
            name=self.get_service_name(),
            action=action,
            parameters=self._service_parameters if self._service_parameters else None
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
            client_ip=self._client_ip,
            services=service_list
        )
        
        return payment_request

    def pay(self, validate: bool = True) -> PaymentResponse:
        """
        Execute the payment operation.
        
        Args:
            validate (bool): Whether to validate service parameters before building
        
        Returns:
            PaymentResponse: Structured payment response object
            
        Raises:
            ValueError: If required fields are missing
            AuthenticationError: If authentication fails
            BuckarooApiError: If API returns an error
        """
        # Build the payment request
        payment_request = self.build("Pay", validate=validate)
        
        # Convert to dictionary for API
        request_data = payment_request.to_dict()

        print(request_data)
        exit()
        return self._post_transaction(request_data)
    
    
    def refund(self, validate: bool = True) -> PaymentResponse:
        """
        Execute a refund transaction.
        
        Args:
            validate (bool): Whether to validate service parameters before building
        
        Returns:
            PaymentResponse: The refund response
            
        Raises:
            ValueError: If required fields are missing
        """
        # Get original_transaction_key from parameter or payload
        txn_key = self._payload.get('original_transaction_key')
        if not txn_key:
            raise ValueError("Original transaction key is required for refunds (provide as parameter or in payload)")
        
        # Get amount from parameter or payload
        refund_amount = self._payload.get('refund_amount')
        
        # Build refund request with original transaction reference
        payment_request = self.build('Refund', validate=validate)
        
        # Convert to dictionary and modify for refund
        request_data = payment_request.to_dict()
        request_data['OriginalTransactionKey'] = txn_key
        
        # Set refund amount if specified, otherwise use original amount
        if refund_amount is not None:
            request_data['AmountCredit'] = refund_amount
            # Remove debit amount for refunds
            if 'AmountDebit' in request_data:
                del request_data['AmountDebit']
        else:
            # Full refund - swap debit to credit
            if 'AmountDebit' in request_data:
                request_data['AmountCredit'] = request_data['AmountDebit']
                del request_data['AmountDebit']
        
        return self._post_transaction(request_data)
    
    def capture(self, original_transaction_key: Optional[str] = None, amount: Optional[float] = None, validate: bool = True) -> PaymentResponse:
        """
        Capture a previously authorized payment.
        
        Args:
            original_transaction_key (str, optional): The transaction key of the authorization.
                                                     If None, will try to get from payload.
            amount (float, optional): Amount to capture. If None, will try to get from payload
                                    or capture the full authorized amount.
            validate (bool): Whether to validate service parameters before building
        
        Returns:
            PaymentResponse: The capture response
        """
        # Get authorization key from parameter or payload
        auth_key = original_transaction_key or self._payload.get('authorization_key') or self._payload.get('original_transaction_key')
        if not auth_key:
            raise ValueError("Authorization key is required for captures (provide as parameter or in payload)")
        
        # Get capture amount from parameter or payload
        capture_amount = amount or self._payload.get('capture_amount')
        
        # Build capture request
        payment_request = self.build('Capture', validate=validate)
        request_data = payment_request.to_dict()
        
        # Set capture-specific parameters
        request_data['OriginalTransactionKey'] = auth_key
        
        # Set capture amount if specified
        if capture_amount is not None:
            request_data['AmountDebit'] = capture_amount
        
        return self._post_transaction(request_data)
    
    def cancel(self, original_transaction_key: Optional[str] = None) -> PaymentResponse:
        """
        Cancel a pending or authorized transaction.
        
        Args:
            original_transaction_key (str, optional): The transaction key to cancel.
                                                     If None, will try to get from payload.
        
        Returns:
            PaymentResponse: The cancellation response
        """
        # Get transaction key from parameter or payload
        txn_key = original_transaction_key or self._payload.get('cancel_key') or self._payload.get('original_transaction_key')
        if not txn_key:
            raise ValueError("Transaction key is required for cancellations (provide as parameter or in payload)")
        
        # Build cancel request
        payment_request = self.build()
        request_data = payment_request.to_dict()
        
        # Set cancellation parameters
        request_data['OriginalTransactionKey'] = txn_key
        # Remove amounts for cancellation
        request_data.pop('AmountDebit', None)
        request_data.pop('AmountCredit', None)
        
        return self._post_transaction(request_data)
    
    def partial_refund(self, original_transaction_key: Optional[str] = None, amount: Optional[float] = None) -> PaymentResponse:
        """
        Execute a partial refund transaction.
        
        Args:
            original_transaction_key (str, optional): The transaction key of the original payment.
                                                     If None, will try to get from payload.
            amount (float, optional): Amount to refund. If None, will try to get from payload.
        
        Returns:
            PaymentResponse: The partial refund response
            
        Raises:
            ValueError: If amount is not provided or invalid
        """
        # Get amount from parameter or payload
        refund_amount = amount or self._payload.get('refund_amount') or self._payload.get('partial_refund_amount')
        if not refund_amount or refund_amount <= 0:
            raise ValueError("Partial refund amount must be greater than 0 (provide as parameter or in payload)")
        
        return self.refund(original_transaction_key, refund_amount)

    def _post_transaction(self, request_data: Dict[str, Any]) -> PaymentResponse:
        """Helper method to post transaction and handle response."""
        # Send to Buckaroo API
        response = self._client.http_client.post('/json/transaction', request_data)
        
        # Check if response is valid and convert to dict
        if response is None:
            # Return a PaymentResponse with empty data for None responses
            return PaymentResponse({})
        
        # Return structured response object
        return PaymentResponse(response.to_dict())
    
    def execute_action(self, action: str, validate: bool = True) -> PaymentResponse:
        """
        Execute a custom action for the payment method.
        
        This is a generic method that can be used for any action supported
        by the payment method (instantRefund, payFastCheckout, etc.).
        
        Args:
            action (str): The action to execute
            validate (bool): Whether to validate service parameters before building
            
        Returns:
            PaymentResponse: The action response
        """
        payment_request = self.build(action, validate=validate)
        request_data = payment_request.to_dict()
        return self._post_transaction(request_data)