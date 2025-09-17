
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