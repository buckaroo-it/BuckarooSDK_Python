from ..factories.solution_method_factory import SolutionMethodFactory
from ..builders.payments.payment_builder import PaymentBuilder


class SolutionService(object):
    """Service for handling solution operations."""

    def __init__(self, client):
        """
        Initialize the SolutionService.

        Args:
            client: The Buckaroo client instance
        """
        self._client = client
        self._factory = SolutionMethodFactory()

    def create_solution(self, method: str, parameters: dict = None) -> PaymentBuilder:
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
            >>> payment = client.solution.create_payment("ideal") \\
            ...     .currency("EUR") \\
            ...     .amount(6.0) \\
            ...     .description("Test payment") \\
            ...     .execute()

            >>> # Using parameters dictionary for quick setup
            >>> payment = client.solution.create_payment("ideal", {
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
            >>> payment = client.solution.create_solution("ideal", {
            ...     'currency': 'EUR',
            ...     'amount': 6.0
            ... }).description("Updated description").execute()
        """
        builder = self._factory.create_builder(method, self._client)

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
        Create a payment builder with auto-detected payment method from payload.

        This method analyzes the payload to automatically determine the appropriate
        payment method and returns the corresponding payment builder.

        Args:
            payload (dict): Payment parameters dictionary

        Returns:
            PaymentBuilder: A builder instance for the detected payment method

        Raises:
            ValueError: If payment method cannot be determined from payload

        Examples:
            >>> # iDEAL payment (auto-detected by 'issuer' field)
            >>> payment = app.payments.create({
            ...     'amount': 25.50,
            ...     'currency': 'EUR',
            ...     'description': 'Test payment',
            ...     'issuer': 'ABNANL2A',
            ...     'return_url': 'https://example.com/success'
            ... })
            >>> response = payment.execute()

            >>> # Credit card payment (auto-detected by card fields)
            >>> payment = app.payments.create({
            ...     'amount': 15.75,
            ...     'currency': 'USD',
            ...     'card_number': '4111111111111111',
            ...     'expiry_month': '12',
            ...     'expiry_year': '2025',
            ...     'cvv': '123'
            ... })
            >>> response = payment.execute()

            >>> # Refund operation (separate method call)
            >>> refund_response = payment.refund('TXN_123', 10.00)
        """
        # Detect payment method from payload
        method = self._factory.detect_method_from_payload(payload)

        # Create payment using the detected method
        return self.create_solution(method, payload)
