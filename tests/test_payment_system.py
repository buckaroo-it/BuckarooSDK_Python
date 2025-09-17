import unittest
from unittest.mock import Mock, patch
from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.services.payment_service import PaymentService
from buckaroo.factories.payment_method_factory import PaymentMethodFactory
from buckaroo.builders.ideal_payment_builder import IdealPaymentBuilder
from buckaroo.builders.creditcard_payment_builder import CreditCardPaymentBuilder
from buckaroo.models.payment_request import PaymentRequest, ClientIP, Service, ServiceList


class TestPaymentSystem(unittest.TestCase):
    """Test suite for the complete payment system."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = BuckarooClient("test_store_key", "test_secret_key")

    def test_client_has_payment_service(self):
        """Test that BuckarooClient has a payments service."""
        self.assertIsInstance(self.client.payments, PaymentService)

    def test_payment_service_initialization(self):
        """Test PaymentService initialization."""
        payment_service = PaymentService(self.client)
        self.assertEqual(payment_service._client, self.client)
        self.assertIsInstance(payment_service._factory, PaymentMethodFactory)

    def test_create_ideal_payment_builder(self):
        """Test creating an iDEAL payment builder."""
        builder = self.client.payments.create_payment("ideal")
        self.assertIsInstance(builder, IdealPaymentBuilder)

    def test_create_creditcard_payment_builder(self):
        """Test creating a credit card payment builder."""
        builder = self.client.payments.create_payment("creditcard")
        self.assertIsInstance(builder, CreditCardPaymentBuilder)

    def test_unsupported_payment_method(self):
        """Test error handling for unsupported payment methods."""
        with self.assertRaises(ValueError) as context:
            self.client.payments.create_payment("unsupported_method")
        
        self.assertIn("Unsupported payment method", str(context.exception))

    def test_get_available_methods(self):
        """Test getting available payment methods."""
        methods = self.client.payments.get_available_methods()
        self.assertIn("ideal", methods)
        self.assertIn("creditcard", methods)
        self.assertIn("paypal", methods)

    def test_is_method_supported(self):
        """Test checking if payment methods are supported."""
        self.assertTrue(self.client.payments.is_method_supported("ideal"))
        self.assertTrue(self.client.payments.is_method_supported("creditcard"))
        self.assertFalse(self.client.payments.is_method_supported("bitcoin"))


class TestPaymentBuilder(unittest.TestCase):
    """Test suite for payment builders."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = BuckarooClient("test_store_key", "test_secret_key")
        self.builder = self.client.payments.create_payment("ideal")

    def test_builder_fluent_interface(self):
        """Test that builder methods return self for chaining."""
        result = (self.builder
                  .currency("EUR")
                  .amount(10.0)
                  .description("Test")
                  .invoice("INV-001"))
        
        self.assertEqual(result, self.builder)

    def test_build_complete_payment_request(self):
        """Test building a complete payment request."""
        payment_request = (self.builder
                          .currency("EUR")
                          .amount(6.0)
                          .description("Test payment")
                          .invoice("INV-123")
                          .return_url("https://example.com/success")
                          .return_url_cancel("https://example.com/cancel")
                          .return_url_error("https://example.com/error")
                          .return_url_reject("https://example.com/reject")
                          .client_ip("192.168.1.1", 1)
                          .build())
        
        self.assertIsInstance(payment_request, PaymentRequest)
        self.assertEqual(payment_request.currency, "EUR")
        self.assertEqual(payment_request.amount_debit, 6.0)
        self.assertEqual(payment_request.description, "Test payment")
        self.assertEqual(payment_request.invoice, "INV-123")
        self.assertEqual(payment_request.client_ip.address, "192.168.1.1")
        self.assertEqual(payment_request.client_ip.type, 1)

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raise ValueError."""
        with self.assertRaises(ValueError) as context:
            self.builder.currency("EUR").build()
        
        self.assertIn("Missing required fields", str(context.exception))

    def test_ideal_builder_with_issuer(self):
        """Test iDEAL builder with issuer parameter."""
        builder = self.client.payments.create_payment("ideal")
        builder.issuer("ABNANL2A")
        
        # Build and check service parameters
        payment_request = (builder
                          .currency("EUR")
                          .amount(10.0)
                          .description("Test")
                          .invoice("INV-001")
                          .return_url("https://example.com/success")
                          .return_url_cancel("https://example.com/cancel")
                          .return_url_error("https://example.com/error")
                          .return_url_reject("https://example.com/reject")
                          .build())
        
        service = payment_request.services.services[0]
        self.assertEqual(service.name, "ideal")
        self.assertEqual(service.parameters["issuer"], "ABNANL2A")

    def test_creditcard_builder_with_card_details(self):
        """Test credit card builder with card details."""
        builder = self.client.payments.create_payment("creditcard")
        
        payment_request = (builder
                          .currency("EUR")
                          .amount(25.0)
                          .description("CC Test")
                          .invoice("CC-001")
                          .return_url("https://example.com/success")
                          .return_url_cancel("https://example.com/cancel")
                          .return_url_error("https://example.com/error")
                          .return_url_reject("https://example.com/reject")
                          .card_number("4111111111111111")
                          .expiry_month("12")
                          .expiry_year("2025")
                          .cvv("123")
                          .build())
        
        service = payment_request.services.services[0]
        self.assertEqual(service.name, "creditcard")
        self.assertEqual(service.parameters["cardNumber"], "4111111111111111")
        self.assertEqual(service.parameters["expiryMonth"], "12")
        self.assertEqual(service.parameters["expiryYear"], "2025")
        self.assertEqual(service.parameters["cvv"], "123")


class TestPaymentModels(unittest.TestCase):
    """Test suite for payment models."""

    def test_client_ip_model(self):
        """Test ClientIP model."""
        client_ip = ClientIP(type=1, address="192.168.1.1")
        expected_dict = {
            "Type": 1,
            "Address": "192.168.1.1"
        }
        self.assertEqual(client_ip.to_dict(), expected_dict)

    def test_service_model(self):
        """Test Service model."""
        service = Service(name="ideal", action="Pay", parameters={"issuer": "ABNANL2A"})
        expected_dict = {
            "Name": "ideal",
            "Action": "Pay",
            "issuer": "ABNANL2A"
        }
        self.assertEqual(service.to_dict(), expected_dict)

    def test_service_list_model(self):
        """Test ServiceList model."""
        service = Service(name="ideal", action="Pay")
        service_list = ServiceList(services=[service])
        expected_dict = {
            "ServiceList": [{"Name": "ideal", "Action": "Pay"}]
        }
        self.assertEqual(service_list.to_dict(), expected_dict)

    def test_payment_request_to_dict_matches_expected_format(self):
        """Test that PaymentRequest.to_dict() matches the expected API format."""
        client_ip = ClientIP(type=0, address="0.0.0.0")
        service = Service(name="ideal", action="Pay")
        service_list = ServiceList(services=[service])
        
        payment_request = PaymentRequest(
            currency="EUR",
            amount_debit=6.0,
            description="Automated test iDEAL with no issuer in the request",
            invoice="Automatedtest_iDEAL_0013",
            return_url="https://www.buckaroo.nl",
            return_url_cancel="https://www.buckaroo.nl/annuleren",
            return_url_error="https://www.buckaroo.nl/mislukt",
            return_url_reject="https://www.buckaroo.nl/geweigerd",
            continue_on_incomplete="1",
            client_ip=client_ip,
            services=service_list
        )
        
        result_dict = payment_request.to_dict()
        
        # Check that all expected keys are present
        expected_keys = [
            "Currency", "AmountDebit", "Description", "Invoice",
            "ReturnURL", "ReturnURLCancel", "ReturnURLError", "ReturnURLReject",
            "ContinueOnIncomplete", "ClientIP", "Services"
        ]
        
        for key in expected_keys:
            self.assertIn(key, result_dict)
        
        # Check specific values
        self.assertEqual(result_dict["Currency"], "EUR")
        self.assertEqual(result_dict["AmountDebit"], 6.0)
        self.assertEqual(result_dict["ClientIP"]["Type"], 0)
        self.assertEqual(result_dict["ClientIP"]["Address"], "0.0.0.0")
        self.assertEqual(result_dict["Services"]["ServiceList"][0]["Name"], "ideal")


class TestPaymentMethodFactory(unittest.TestCase):
    """Test suite for PaymentMethodFactory."""

    def test_factory_create_payment_builder(self):
        """Test factory creating payment builders."""
        client = Mock()
        
        builder = PaymentMethodFactory.create_payment_builder("ideal", client)
        self.assertIsInstance(builder, IdealPaymentBuilder)

    def test_factory_unsupported_method(self):
        """Test factory with unsupported payment method."""
        client = Mock()
        
        with self.assertRaises(ValueError):
            PaymentMethodFactory.create_payment_builder("unsupported", client)

    def test_factory_case_insensitive(self):
        """Test that factory is case insensitive."""
        client = Mock()
        
        builder1 = PaymentMethodFactory.create_payment_builder("IDEAL", client)
        builder2 = PaymentMethodFactory.create_payment_builder("ideal", client)
        
        self.assertEqual(type(builder1), type(builder2))

    def test_factory_get_available_methods(self):
        """Test getting available methods from factory."""
        methods = PaymentMethodFactory.get_available_methods()
        self.assertIn("ideal", methods)
        self.assertIn("creditcard", methods)
        self.assertIn("paypal", methods)

    def test_factory_is_method_supported(self):
        """Test checking method support."""
        self.assertTrue(PaymentMethodFactory.is_method_supported("ideal"))
        self.assertFalse(PaymentMethodFactory.is_method_supported("bitcoin"))


if __name__ == '__main__':
    unittest.main()