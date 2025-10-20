
from typing import Dict, Any
from ..factories.payment_method_factory import PaymentMethodFactory
from ..builders.payment_builder import PaymentBuilder


class PaymentService(object):
    """Service for handling payment operations."""
    
    def __init__(self, client):
        """
        Initialize the PaymentService.
        
        Args:
            client: The Buckaroo client instance
        """
        self._client = client
        self._factory = PaymentMethodFactory()
    
    def create_payment(self, method: str, parameters: dict = None) -> PaymentBuilder:
        """
        Create a payment builder for the specified method.
        
        Args:
            method (str): The payment method name (e.g., 'ideal', 'creditcard', 'paypal')
            parameters (dict, optional): Dictionary of parameters to pre-populate the builder
            
        Returns:
            PaymentBuilder: A builder instance for the specified payment method
            
        Raises:
            ValueError: If the payment method is not supported
            
        Example:
            >>> # Using fluent interface only
            >>> payment = client.payments.create_payment("ideal") \\
            ...     .currency("EUR") \\
            ...     .amount(6.0) \\
            ...     .description("Test payment") \\
            ...     .execute()
            
            >>> # Using parameters dictionary for quick setup
            >>> payment = client.payments.create_payment("ideal", {
            ...     'currency': 'EUR',
            ...     'amount': 6.0,
            ...     'description': 'Test payment',
            ...     'invoice': 'INV-123',
            ...     'return_url': 'https://example.com/success',
            ...     'return_url_cancel': 'https://example.com/cancel',
            ...     'return_url_error': 'https://example.com/error',
            ...     'return_url_reject': 'https://example.com/reject'
            ... }).execute()
            
            >>> # Combining both approaches
            >>> payment = client.payments.create_payment("ideal", {
            ...     'currency': 'EUR',
            ...     'amount': 6.0
            ... }).description("Updated description").execute()
        """
        builder = self._factory.create_payment_builder(method, self._client)
        
        # If parameters are provided, populate the builder
        if parameters:
            builder.from_dict(parameters)
            
        return builder
    
    def get_available_methods(self) -> list:
        """
        Get a list of all available payment methods.
        
        Returns:
            list: List of available payment method names
        """
        return self._factory.get_available_methods()
    
    def is_method_supported(self, method: str) -> bool:
        """
        Check if a payment method is supported.
        
        Args:
            method (str): The payment method name
            
        Returns:
            bool: True if the method is supported, False otherwise
        """
        return self._factory.is_method_supported(method)
    
    def create(self, payload: dict) -> PaymentBuilder:
        """
        Smart payment creation that auto-detects payment method and operation from payload.
        
        This method analyzes the payload to automatically determine the appropriate
        payment method and operation type, then returns the corresponding payment builder.
        
        Args:
            payload (dict): Payment parameters dictionary
            
        Returns:
            PaymentBuilder: A builder instance configured for the detected method and operation
            
        Raises:
            ValueError: If payment method cannot be determined from payload
            
        Examples:
            >>> # iDEAL payment (auto-detected by 'issuer' field)
            >>> payment = app.payment.create({
            ...     'amount': 25.50,
            ...     'currency': 'EUR',
            ...     'description': 'Test payment',
            ...     'issuer': 'ABNANL2A',
            ...     'return_url': 'https://example.com/success'
            ... })
            >>> response = payment.pay()
            
            >>> # Refund (auto-detected by 'original_transaction_key')
            >>> refund = app.payment.create({
            ...     'original_transaction_key': 'TXN_123',
            ...     'refund_amount': 15.75,
            ...     'currency': 'EUR',
            ...     'description': 'Refund for order #123'
            ... })
            >>> response = refund.pay()  # Executes refund
            
            >>> # Capture (auto-detected by 'authorization_key')
            >>> capture = app.payment.create({
            ...     'authorization_key': 'AUTH_456', 
            ...     'capture_amount': 50.00,
            ...     'currency': 'USD'
            ... })
            >>> response = capture.pay()  # Executes capture
            
            >>> # Cancel (auto-detected by 'cancel_key')
            >>> cancel = app.payment.create({
            ...     'cancel_key': 'PENDING_789',
            ...     'description': 'Cancel pending payment'
            ... })
            >>> response = cancel.pay()  # Executes cancellation
        """
        # Detect operation type from payload
        operation = self._factory.detect_operation_from_payload(payload)
        
        # For operations other than 'pay', we need a payment method for the builder
        # but we can use a generic one since the operation will override the action
        if operation != 'pay':
            # Try to detect method, fallback to 'ideal' for operations
            try:
                method = self._factory.detect_payment_method_from_payload(payload)
            except ValueError:
                # For operations, method is less important, use ideal as default
                method = 'ideal'
        else:
            # For payments, method detection is critical
            method = self._factory.detect_payment_method_from_payload(payload)
        
        # Create payment builder
        builder = self.create_payment(method, payload)
        
        # Configure builder for the specific operation
        if operation == 'refund':
            builder._operation_type = 'refund'
            builder._original_transaction_key = payload.get('original_transaction_key')
            builder._operation_amount = payload.get('refund_amount')
        elif operation == 'capture':
            builder._operation_type = 'capture' 
            builder._original_transaction_key = payload.get('authorization_key')
            builder._operation_amount = payload.get('capture_amount')
        elif operation == 'cancel':
            builder._operation_type = 'cancel'
            builder._original_transaction_key = payload.get('cancel_key')
        else:
            builder._operation_type = 'pay'
            
        return builder