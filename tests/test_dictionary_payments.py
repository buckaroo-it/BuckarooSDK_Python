import unittest
from unittest.mock import Mock
from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.services.payment_service import PaymentService
from buckaroo.builders.ideal_payment_builder import IdealPaymentBuilder
from buckaroo.builders.creditcard_payment_builder import CreditCardPaymentBuilder
from buckaroo.models.payment_request import PaymentRequest


class TestDictionaryPaymentCreation(unittest.TestCase):
    """Test suite for dictionary-based payment creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = BuckarooClient("test_store_key", "test_secret_key")

    def test_create_payment_with_dictionary_parameters(self):
        """Test creating payment with dictionary parameters."""
        params = {
            'currency': 'EUR',
            'amount': 10.0,
            'description': 'Test payment',
            'invoice': 'INV-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject'
        }
        
        builder = self.client.payments.create_payment("ideal", params)
        self.assertIsInstance(builder, IdealPaymentBuilder)
        
        # Build the payment and verify parameters were set
        payment_request = builder.build()
        self.assertEqual(payment_request.currency, "EUR")
        self.assertEqual(payment_request.amount_debit, 10.0)
        self.assertEqual(payment_request.description, "Test payment")
        self.assertEqual(payment_request.invoice, "INV-001")

    def test_create_payment_without_dictionary_parameters(self):
        """Test creating payment without dictionary parameters (backward compatibility)."""
        builder = self.client.payments.create_payment("ideal")
        self.assertIsInstance(builder, IdealPaymentBuilder)
        
        # Should be able to use fluent interface
        builder.currency("EUR").amount(10.0)
        self.assertEqual(builder._currency, "EUR")
        self.assertEqual(builder._amount_debit, 10.0)

    def test_dictionary_with_client_ip_string(self):
        """Test dictionary with client IP as string."""
        params = {
            'currency': 'EUR',
            'amount': 10.0,
            'description': 'Test payment',
            'invoice': 'INV-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject',
            'client_ip': '192.168.1.1'
        }
        
        builder = self.client.payments.create_payment("ideal", params)
        payment_request = builder.build()
        
        self.assertEqual(payment_request.client_ip.address, "192.168.1.1")
        self.assertEqual(payment_request.client_ip.type, 0)  # Default type

    def test_dictionary_with_client_ip_dict(self):
        """Test dictionary with client IP as dictionary."""
        params = {
            'currency': 'EUR',
            'amount': 10.0,
            'description': 'Test payment',
            'invoice': 'INV-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject',
            'client_ip': {'address': '192.168.1.1', 'type': 1}
        }
        
        builder = self.client.payments.create_payment("ideal", params)
        payment_request = builder.build()
        
        self.assertEqual(payment_request.client_ip.address, "192.168.1.1")
        self.assertEqual(payment_request.client_ip.type, 1)

    def test_dictionary_with_service_parameters(self):
        """Test dictionary with service-specific parameters."""
        params = {
            'currency': 'EUR',
            'amount': 10.0,
            'description': 'Test payment',
            'invoice': 'INV-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject',
            'service_parameters': {
                'customParam1': 'value1',
                'customParam2': 'value2'
            }
        }
        
        builder = self.client.payments.create_payment("ideal", params)
        payment_request = builder.build()
        
        service = payment_request.services.services[0]
        self.assertEqual(service.parameters['customParam1'], 'value1')
        self.assertEqual(service.parameters['customParam2'], 'value2')

    def test_ideal_dictionary_with_issuer(self):
        """Test iDEAL payment with issuer in dictionary."""
        params = {
            'currency': 'EUR',
            'amount': 10.0,
            'description': 'Test payment',
            'invoice': 'INV-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject',
            'issuer': 'ABNANL2A'
        }
        
        builder = self.client.payments.create_payment("ideal", params)
        payment_request = builder.build()
        
        service = payment_request.services.services[0]
        self.assertEqual(service.parameters['issuer'], 'ABNANL2A')

    def test_creditcard_dictionary_with_card_details(self):
        """Test credit card payment with card details in dictionary."""
        params = {
            'currency': 'EUR',
            'amount': 25.0,
            'description': 'CC Test',
            'invoice': 'CC-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject',
            'card_number': '4111111111111111',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvv': '123'
        }
        
        builder = self.client.payments.create_payment("creditcard", params)
        payment_request = builder.build()
        
        service = payment_request.services.services[0]
        self.assertEqual(service.parameters['cardNumber'], '4111111111111111')
        self.assertEqual(service.parameters['expiryMonth'], '12')
        self.assertEqual(service.parameters['expiryYear'], '2025')
        self.assertEqual(service.parameters['cvv'], '123')

    def test_creditcard_dictionary_with_service_parameters(self):
        """Test credit card payment with service_parameters in dictionary."""
        params = {
            'currency': 'EUR',
            'amount': 25.0,
            'description': 'CC Test',
            'invoice': 'CC-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject',
            'service_parameters': {
                'cardNumber': '4111111111111111',
                'expiryMonth': '12',
                'expiryYear': '2025',
                'cvv': '123'
            }
        }
        
        builder = self.client.payments.create_payment("creditcard", params)
        payment_request = builder.build()
        
        service = payment_request.services.services[0]
        self.assertEqual(service.parameters['cardNumber'], '4111111111111111')
        self.assertEqual(service.parameters['expiryMonth'], '12')
        self.assertEqual(service.parameters['expiryYear'], '2025')
        self.assertEqual(service.parameters['cvv'], '123')

    def test_combined_dictionary_and_fluent_interface(self):
        """Test combining dictionary parameters with fluent interface."""
        params = {
            'currency': 'EUR',
            'amount': 10.0,
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject'
        }
        
        builder = (self.client.payments.create_payment("ideal", params)
                  .description("Overridden description")  # Override with fluent
                  .invoice("FLUENT-001")  # Add with fluent
                  .client_ip("192.168.1.1", 1))  # Override with fluent
        
        payment_request = builder.build()
        
        # Check that fluent interface values override/add to dictionary values
        self.assertEqual(payment_request.currency, "EUR")  # From dictionary
        self.assertEqual(payment_request.amount_debit, 10.0)  # From dictionary
        self.assertEqual(payment_request.description, "Overridden description")  # From fluent
        self.assertEqual(payment_request.invoice, "FLUENT-001")  # From fluent
        self.assertEqual(payment_request.client_ip.address, "192.168.1.1")  # From fluent
        self.assertEqual(payment_request.client_ip.type, 1)  # From fluent

    def test_fluent_interface_overrides_dictionary(self):
        """Test that fluent interface methods override dictionary values."""
        params = {
            'currency': 'USD',
            'amount': 10.0,
            'description': 'Original description'
        }
        
        builder = (self.client.payments.create_payment("ideal", params)
                  .currency("EUR")  # Override currency
                  .amount(20.0)  # Override amount
                  .description("New description")  # Override description
                  .invoice("INV-001")
                  .return_url("https://example.com/success")
                  .return_url_cancel("https://example.com/cancel")
                  .return_url_error("https://example.com/error")
                  .return_url_reject("https://example.com/reject"))
        
        payment_request = builder.build()
        
        # Fluent interface should override dictionary values
        self.assertEqual(payment_request.currency, "EUR")
        self.assertEqual(payment_request.amount_debit, 20.0)
        self.assertEqual(payment_request.description, "New description")

    def test_partial_dictionary_completion_with_fluent(self):
        """Test using dictionary for some parameters and fluent for required missing ones."""
        params = {
            'currency': 'EUR',
            'amount': 10.0,
            'description': 'Partial setup'
        }
        
        builder = (self.client.payments.create_payment("ideal", params)
                  .invoice("PARTIAL-001")  # Add missing required field
                  .return_url("https://example.com/success")  # Add missing required field
                  .return_url_cancel("https://example.com/cancel")  # Add missing required field
                  .return_url_error("https://example.com/error")  # Add missing required field
                  .return_url_reject("https://example.com/reject"))  # Add missing required field
        
        # Should not raise validation error since all required fields are now set
        payment_request = builder.build()
        self.assertIsInstance(payment_request, PaymentRequest)


class TestBuilderFromDict(unittest.TestCase):
    """Test suite for PaymentBuilder from_dict method."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = BuckarooClient("test_store_key", "test_secret_key")

    def test_from_dict_with_all_parameters(self):
        """Test from_dict with all supported parameters."""
        data = {
            'currency': 'EUR',
            'amount': 15.50,
            'description': 'Complete test payment',
            'invoice': 'COMPLETE-001',
            'return_url': 'https://example.com/success',
            'return_url_cancel': 'https://example.com/cancel',
            'return_url_error': 'https://example.com/error',
            'return_url_reject': 'https://example.com/reject',
            'continue_on_incomplete': '0',
            'client_ip': {'address': '10.0.0.1', 'type': 2},
            'service_parameters': {'param1': 'value1', 'param2': 'value2'}
        }
        
        builder = self.client.payments.create_payment("ideal")
        builder.from_dict(data)
        
        # Verify all parameters were set
        self.assertEqual(builder._currency, 'EUR')
        self.assertEqual(builder._amount_debit, 15.50)
        self.assertEqual(builder._description, 'Complete test payment')
        self.assertEqual(builder._invoice, 'COMPLETE-001')
        self.assertEqual(builder._return_url, 'https://example.com/success')
        self.assertEqual(builder._return_url_cancel, 'https://example.com/cancel')
        self.assertEqual(builder._return_url_error, 'https://example.com/error')
        self.assertEqual(builder._return_url_reject, 'https://example.com/reject')
        self.assertEqual(builder._continue_on_incomplete, '0')
        self.assertEqual(builder._client_ip.address, '10.0.0.1')
        self.assertEqual(builder._client_ip.type, 2)
        self.assertEqual(builder._service_parameters['param1'], 'value1')
        self.assertEqual(builder._service_parameters['param2'], 'value2')

    def test_from_dict_returns_self(self):
        """Test that from_dict returns self for method chaining."""
        data = {'currency': 'EUR', 'amount': 10.0}
        builder = self.client.payments.create_payment("ideal")
        result = builder.from_dict(data)
        
        self.assertEqual(result, builder)

    def test_from_dict_with_empty_dictionary(self):
        """Test from_dict with empty dictionary."""
        builder = self.client.payments.create_payment("ideal")
        result = builder.from_dict({})
        
        # Should not raise error and should return self
        self.assertEqual(result, builder)


if __name__ == '__main__':
    unittest.main()