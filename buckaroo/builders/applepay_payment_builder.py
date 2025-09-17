"""
Apple Pay Payment Builder for Buckaroo SDK.

This module provides the ApplePayPaymentBuilder class for creating Apple Pay payments
with Buckaroo's payment gateway. Apple Pay uses encrypted payment data from iOS devices
to process secure payments.
"""

from typing import Dict, Any
from .payment_builder import PaymentBuilder
from ..models.payment_request import Parameter


class ApplePayPaymentBuilder(PaymentBuilder):
    """
    Builder for Apple Pay payments.
    
    Apple Pay payments require encrypted payment data from the Apple Pay framework
    and optionally the customer's card name. The payment uses the 'Pay' action
    to process the payment immediately.
    
    Example:
        >>> builder = client.payments.create_payment("applepay")
        >>> payment = (builder
        ...     .payment_data("encrypted_payment_data_from_apple_pay")
        ...     .customer_card_name("John Doe")
        ...     .invoice("INV-001")
        ...     .currency("EUR")
        ...     .amount_debit(25.00))
    """
    
    def __init__(self, client):
        """
        Initialize the Apple Pay payment builder.
        
        Args:
            client: The Buckaroo client instance.
        """
        super().__init__(client)
        self._payment_data: str = None
        self._customer_card_name: str = None
    
    def get_service_name(self) -> str:
        """
        Get the service name for Apple Pay.
        
        Returns:
            str: The service name "applepay".
        """
        return "applepay"
    
    def get_action(self) -> str:
        """
        Get the action for Apple Pay payments.
        
        Returns:
            str: The action "Pay".
        """
        return "Pay"
    
    def payment_data(self, payment_data: str) -> 'ApplePayPaymentBuilder':
        """
        Set the Apple Pay payment data.
        
        This is the encrypted payment data received from the Apple Pay framework
        when the user authorizes the payment on their iOS device.
        
        Args:
            payment_data (str): The encrypted payment data from Apple Pay.
            
        Returns:
            ApplePayPaymentBuilder: Self for method chaining.
        """
        self._payment_data = payment_data
        self.add_apple_pay_parameter("PaymentData", payment_data)
        return self
    
    def customer_card_name(self, card_name: str) -> 'ApplePayPaymentBuilder':
        """
        Set the customer card name.
        
        Args:
            card_name (str): The name on the customer's card.
            
        Returns:
            ApplePayPaymentBuilder: Self for method chaining.
        """
        self._customer_card_name = card_name
        self.add_apple_pay_parameter("CustomerCardName", card_name)
        return self
    
    def add_apple_pay_parameter(self, name: str, value: str, group_type: str = "", group_id: str = "") -> 'ApplePayPaymentBuilder':
        """
        Add a parameter to the Apple Pay service.
        
        Args:
            name (str): Parameter name.
            value (str): Parameter value.
            group_type (str, optional): Parameter group type. Defaults to "".
            group_id (str, optional): Parameter group ID. Defaults to "".
            
        Returns:
            ApplePayPaymentBuilder: Self for method chaining.
        """
        parameter = Parameter(
            name=name,
            value=str(value),
            group_type=group_type,
            group_id=group_id
        )
        self._parameters.append(parameter)
        return self
    
    def from_dict(self, data: Dict[str, Any]) -> 'ApplePayPaymentBuilder':
        """
        Configure the builder from a dictionary of parameters.
        
        Supported dictionary keys:
        - payment_data: Apple Pay encrypted payment data
        - customer_card_name: Customer's card name
        - service_parameters: Dict of additional service parameters
        
        Args:
            data (Dict[str, Any]): Dictionary containing payment parameters.
            
        Returns:
            ApplePayPaymentBuilder: Self for method chaining.
            
        Example:
            >>> params = {
            ...     'payment_data': 'encrypted_data',
            ...     'customer_card_name': 'John Doe',
            ...     'currency': 'EUR',
            ...     'amount_debit': 25.00
            ... }
            >>> builder = client.payments.create_payment("applepay", params)
        """
        # Call parent from_dict for common parameters
        super().from_dict(data)
        
        # Handle Apple Pay specific parameters
        if 'payment_data' in data:
            self.payment_data(data['payment_data'])
            
        if 'customer_card_name' in data:
            self.customer_card_name(data['customer_card_name'])
        
        # Handle service_parameters for Apple Pay
        if 'service_parameters' in data:
            service_params = data['service_parameters']
            if isinstance(service_params, dict):
                if 'PaymentData' in service_params:
                    self.payment_data(service_params['PaymentData'])
                if 'CustomerCardName' in service_params:
                    self.customer_card_name(service_params['CustomerCardName'])
                    
                # Add any other parameters
                for key, value in service_params.items():
                    if key not in ['PaymentData', 'CustomerCardName']:
                        self.add_apple_pay_parameter(key, value)
        
        return self
    
    def _validate_required_fields(self) -> None:
        """
        Validate that all required fields are set.
        
        Raises:
            ValueError: If required Apple Pay fields are missing.
        """
        # Call parent validation for common fields
        super()._validate_required_fields()
        
        # Apple Pay specific validation
        missing_fields = []
        
        if not self._payment_data:
            missing_fields.append("PaymentData")
        
        if missing_fields:
            raise ValueError(f"Missing required Apple Pay parameters: {', '.join(missing_fields)}")
    
    def _build_service(self):
        """
        Build the Apple Pay service configuration.
        
        Returns:
            Service: The configured Apple Pay service.
        """
        from ..models.payment_request import Service
        
        return Service(
            name=self.get_service_name(),
            action=self.get_action(),
            parameters=self._parameters.copy()
        )