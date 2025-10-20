from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from ..models.payment_request import PaymentRequest, ClientIP, Service, ServiceList, Parameter
from ..models.payment_response import PaymentResponse


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
        self._service_parameters: Dict[str, Any] = {}
        
        # Operation-specific attributes
        self._operation_type: str = 'pay'
        self._original_transaction_key: Optional[str] = None
        self._operation_amount: Optional[float] = None
    
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
        self._service_parameters[key] = value
        return self
    
    def from_dict(self, data: Dict[str, Any]) -> 'PaymentBuilder':
        """
        Populate the builder from a dictionary of parameters.
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters
            
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
                for key, value in service_params.items():
                    self.add_parameter(key, value)
        
        return self
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get the service name for this payment method."""
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
    
    def build(self, action = "Pay") -> PaymentRequest:
        """Build the payment request."""
        self._validate_required_fields()
        
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
    
    def pay(self) -> PaymentResponse:
        """
        Execute the payment operation based on the configured operation type.
        
        This method automatically detects the operation type from the payload
        and executes the appropriate action (pay, refund, capture, cancel).
        
        Returns:
            PaymentResponse: Structured payment response object
            
        Raises:
            ValueError: If required fields are missing
            AuthenticationError: If authentication fails
            BuckarooApiError: If API returns an error
        """
        # Build the payment request
        payment_request = self.build()
        
        # Convert to dictionary for API
        request_data = payment_request.to_dict()
        
        # Send to Buckaroo API
        response = self._client.http_client.post('/json/transaction', request_data)
        
        # Return structured response object
        return PaymentResponse(response.to_dict())
    
    
    def refund(self) -> PaymentResponse:
        """Execute a refund transaction."""
        # Build base request
        payment_request = self.build("Refund")
        request_data = payment_request.to_dict()
        
        # Set refund-specific parameters
        request_data['OriginalTransactionKey'] = self._original_transaction_key

        # Handle amount for refund
        if self._operation_amount is not None:
            request_data['AmountCredit'] = self._operation_amount
            request_data.pop('AmountDebit', None)
        else:
            # Full refund - swap debit to credit
            if 'AmountDebit' in request_data:
                request_data['AmountCredit'] = request_data['AmountDebit']
                del request_data['AmountDebit']
        
        # Send refund request
        response = self._client.http_client.post('/json/transaction', request_data)

        print(response.to_dict())
        exit()
        return PaymentResponse(response.to_dict())
    
    def capture(self) -> PaymentResponse:
        """Execute a capture transaction."""
        # Build base request
        payment_request = self.build()
        request_data = payment_request.to_dict()
        
        # Set capture-specific parameters
        request_data['OriginalTransactionKey'] = self._original_transaction_key
        
        # Set capture amount if specified
        if self._operation_amount is not None:
            request_data['AmountDebit'] = self._operation_amount
        
        # Send capture request
        response = self._client.http_client.post('/json/transaction', request_data)
        return PaymentResponse(response.to_dict())
    
    def cancel(self) -> PaymentResponse:
        """Execute a cancellation transaction."""
        # Build base request
        payment_request = self.build()
        request_data = payment_request.to_dict()
        
        # Set cancellation parameters
        request_data['OriginalTransactionKey'] = self._original_transaction_key
        # Remove amounts for cancellation
        request_data.pop('AmountDebit', None)
        request_data.pop('AmountCredit', None)
        
        # Send cancellation request
        response = self._client.http_client.post('/json/transaction', request_data)
        return PaymentResponse(response.to_dict())
    
    def partial_refund(self, original_transaction_key: str, amount: float) -> PaymentResponse:
        """
        Execute a partial refund transaction.
        
        Args:
            original_transaction_key (str): The transaction key of the original payment
            amount (float): Amount to refund (must be less than original amount)
        
        Returns:
            PaymentResponse: The partial refund response
            
        Raises:
            ValueError: If amount is not provided or invalid
        """
        if not amount or amount <= 0:
            raise ValueError("Partial refund amount must be greater than 0")
        
        return self.refund(original_transaction_key, amount)
    
    def cancel(self, original_transaction_key: str) -> PaymentResponse:
        """
        Cancel a pending or authorized transaction.
        
        Args:
            original_transaction_key (str): The transaction key to cancel
        
        Returns:
            PaymentResponse: The cancellation response
        """
        if not original_transaction_key:
            raise ValueError("Original transaction key is required for cancellations")
        
        # Build cancel request
        payment_request = self.build()
        request_data = payment_request.to_dict()
        
        # Set cancellation parameters
        request_data['OriginalTransactionKey'] = original_transaction_key
        # Remove amounts for cancellation
        request_data.pop('AmountDebit', None)
        request_data.pop('AmountCredit', None)
        
        # Send cancellation request
        response = self._client.http_client.post('/json/transaction', request_data)
        
        return PaymentResponse(response.to_dict())