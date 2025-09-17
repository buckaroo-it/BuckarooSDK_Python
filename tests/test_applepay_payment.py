import unittest
from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.applepay_payment_builder import ApplePayPaymentBuilder
from buckaroo.models.payment_request import Parameter


class TestApplePayPaymentBuilder(unittest.TestCase):
    """Test suite for Apple Pay payment builder."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = BuckarooClient("test_store_key", "test_secret_key")
        self.sample_payment_data = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcHBsZXBheSJ9"
        self.sample_card_name = "John Doe"

    def test_create_applepay_payment_builder(self):
        """Test creating an Apple Pay payment builder."""
        builder = self.client.payments.create_payment("applepay")
        self.assertIsInstance(builder, ApplePayPaymentBuilder)

    def test_applepay_service_name_and_action(self):
        """Test Apple Pay service name and action."""
        builder = self.client.payments.create_payment("applepay")
        self.assertEqual(builder.get_service_name(), "applepay")
        self.assertEqual(builder.get_action(), "Pay")

    def test_add_apple_pay_parameter(self):
        """Test adding Apple Pay-specific parameters."""
        builder = self.client.payments.create_payment("applepay")
        builder.add_apple_pay_parameter("TestParam", "TestValue", "TestGroup", "TestID")
        
        self.assertEqual(len(builder._parameters), 1)
        param = builder._parameters[0]
        self.assertEqual(param.name, "TestParam")
        self.assertEqual(param.value, "TestValue")
        self.assertEqual(param.group_type, "TestGroup")
        self.assertEqual(param.group_id, "TestID")

    def test_applepay_fluent_interface(self):
        """Test Apple Pay fluent interface methods."""
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(self.sample_payment_data)
                  .customer_card_name(self.sample_card_name))
        
        # Verify parameters were added
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["PaymentData"], self.sample_payment_data)
        self.assertEqual(param_dict["CustomerCardName"], self.sample_card_name)

    def test_applepay_from_dict(self):
        """Test creating Apple Pay payment from dictionary."""
        params = {
            'payment_data': self.sample_payment_data,
            'customer_card_name': self.sample_card_name,
            'currency': 'EUR',
            'amount_debit': 25.00,
            'invoice': 'INV-001'
        }
        
        builder = self.client.payments.create_payment("applepay", params)
        
        # Verify service parameters were set
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["PaymentData"], self.sample_payment_data)
        self.assertEqual(param_dict["CustomerCardName"], self.sample_card_name)
        
        # Verify payment request fields
        payment_request = builder.build()
        self.assertEqual(payment_request.currency, "EUR")
        self.assertEqual(payment_request.amount_debit, 25.00)
        self.assertEqual(payment_request.invoice, "INV-001")

    def test_applepay_from_dict_with_service_parameters(self):
        """Test creating Apple Pay payment with service_parameters dict."""
        params = {
            'currency': 'USD',
            'amount_debit': 15.50,
            'service_parameters': {
                'PaymentData': self.sample_payment_data,
                'CustomerCardName': self.sample_card_name,
                'CustomParam': 'CustomValue'
            }
        }
        
        builder = self.client.payments.create_payment("applepay", params)
        
        # Verify parameters were set
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["PaymentData"], self.sample_payment_data)
        self.assertEqual(param_dict["CustomerCardName"], self.sample_card_name)
        self.assertEqual(param_dict["CustomParam"], "CustomValue")

    def test_applepay_build_complete_request(self):
        """Test building a complete Apple Pay request."""
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(self.sample_payment_data)
                  .customer_card_name(self.sample_card_name)
                  .currency("EUR")
                  .amount_debit(25.00)
                  .invoice("10000480"))
        
        payment_request = builder.build()
        
        # Check payment request fields
        self.assertEqual(payment_request.currency, "EUR")
        self.assertEqual(payment_request.amount_debit, 25.00)
        self.assertEqual(payment_request.invoice, "10000480")
        
        # Check service structure
        self.assertEqual(len(payment_request.services.services), 1)
        service = payment_request.services.services[0]
        self.assertEqual(service.name, "applepay")
        self.assertEqual(service.action, "Pay")
        self.assertIsInstance(service.parameters, list)
        self.assertEqual(len(service.parameters), 2)

    def test_applepay_to_dict_matches_expected_format(self):
        """Test that Apple Pay generates the expected JSON format."""
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(self.sample_payment_data)
                  .customer_card_name(self.sample_card_name)
                  .currency("EUR")
                  .amount_debit(1.00)
                  .invoice("10000480"))
        
        payment_request = builder.build()
        result_dict = payment_request.to_dict()
        
        # Check top-level structure
        self.assertEqual(result_dict["Currency"], "EUR")
        self.assertEqual(result_dict["AmountDebit"], 1.00)
        self.assertEqual(result_dict["Invoice"], "10000480")
        
        # Check Services structure
        self.assertIn("Services", result_dict)
        services = result_dict["Services"]
        self.assertIn("ServiceList", services)
        
        service_list = services["ServiceList"]
        self.assertEqual(len(service_list), 1)
        
        service = service_list[0]
        self.assertEqual(service["Name"], "applepay")
        self.assertEqual(service["Action"], "Pay")
        self.assertIn("Parameters", service)
        
        # Check parameters structure
        parameters = service["Parameters"]
        self.assertEqual(len(parameters), 2)
        
        # Verify parameter structure
        param_names = [param["Name"] for param in parameters]
        self.assertIn("PaymentData", param_names)
        self.assertIn("CustomerCardName", param_names)
        
        # Check specific parameter format
        payment_data_param = next(p for p in parameters if p["Name"] == "PaymentData")
        self.assertEqual(payment_data_param["Value"], self.sample_payment_data)
        self.assertEqual(payment_data_param["GroupType"], "")
        self.assertEqual(payment_data_param["GroupID"], "")
        
        card_name_param = next(p for p in parameters if p["Name"] == "CustomerCardName")
        self.assertEqual(card_name_param["Value"], self.sample_card_name)
        self.assertEqual(card_name_param["GroupType"], "")
        self.assertEqual(card_name_param["GroupID"], "")

    def test_applepay_validation_missing_payment_data(self):
        """Test validation with missing PaymentData."""
        builder = (self.client.payments.create_payment("applepay")
                  .customer_card_name(self.sample_card_name)
                  .currency("EUR")
                  .amount_debit(25.00))
        
        with self.assertRaises(ValueError) as context:
            builder.build()
        
        self.assertIn("Missing required Apple Pay parameters: PaymentData", str(context.exception))

    def test_applepay_validation_with_required_fields(self):
        """Test validation passes with required fields."""
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(self.sample_payment_data)
                  .currency("EUR")
                  .amount_debit(25.00))
        
        # Should not raise validation error
        payment_request = builder.build()
        self.assertIsNotNone(payment_request)

    def test_applepay_execute(self):
        """Test executing Apple Pay payment."""
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(self.sample_payment_data)
                  .customer_card_name(self.sample_card_name)
                  .currency("EUR")
                  .amount_debit(25.00)
                  .invoice("10000480"))
        
        result = builder.execute()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("payment_request", result)

    def test_applepay_combined_dictionary_and_fluent(self):
        """Test combining dictionary and fluent interface for Apple Pay."""
        params = {
            'payment_data': self.sample_payment_data,
            'currency': 'USD',
            'amount_debit': 15.00
        }
        
        builder = (self.client.payments.create_payment("applepay", params)
                  .customer_card_name(self.sample_card_name)  # Add via fluent
                  .invoice("COMBO-001"))  # Add via fluent
        
        payment_request = builder.build()
        param_dict = {param.name: param.value for param in builder._parameters}
        
        # Should have both dict and fluent values
        self.assertEqual(param_dict["PaymentData"], self.sample_payment_data)
        self.assertEqual(param_dict["CustomerCardName"], self.sample_card_name)
        self.assertEqual(payment_request.currency, "USD")
        self.assertEqual(payment_request.amount_debit, 15.00)
        self.assertEqual(payment_request.invoice, "COMBO-001")

    def test_applepay_custom_parameters(self):
        """Test adding custom parameters to Apple Pay."""
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(self.sample_payment_data)
                  .customer_card_name(self.sample_card_name))
        
        # Add custom parameters
        builder.add_apple_pay_parameter("CustomField1", "CustomValue1", "CustomGroup", "Group1")
        builder.add_apple_pay_parameter("CustomField2", "CustomValue2")
        
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["CustomField1"], "CustomValue1")
        self.assertEqual(param_dict["CustomField2"], "CustomValue2")
        
        # Check group information
        custom_param1 = next(p for p in builder._parameters if p.name == "CustomField1")
        self.assertEqual(custom_param1.group_type, "CustomGroup")
        self.assertEqual(custom_param1.group_id, "Group1")
        
        custom_param2 = next(p for p in builder._parameters if p.name == "CustomField2")
        self.assertEqual(custom_param2.group_type, "")
        self.assertEqual(custom_param2.group_id, "")

    def test_applepay_payment_data_only(self):
        """Test Apple Pay with only payment data (minimal requirements)."""
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(self.sample_payment_data)
                  .currency("EUR")
                  .amount_debit(10.00))
        
        payment_request = builder.build()
        
        # Should build successfully with minimal requirements
        self.assertIsNotNone(payment_request)
        
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["PaymentData"], self.sample_payment_data)
        self.assertNotIn("CustomerCardName", param_dict)

    def test_applepay_parameter_value_conversion(self):
        """Test parameter value conversion to string."""
        builder = self.client.payments.create_payment("applepay")
        
        # Test with different data types
        builder.add_apple_pay_parameter("NumericParam", 123)
        builder.add_apple_pay_parameter("BooleanParam", True)
        builder.add_apple_pay_parameter("FloatParam", 45.67)
        
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["NumericParam"], "123")
        self.assertEqual(param_dict["BooleanParam"], "True")
        self.assertEqual(param_dict["FloatParam"], "45.67")

    def test_applepay_real_world_scenario(self):
        """Test a real-world Apple Pay payment scenario."""
        # Simulate a real Apple Pay transaction
        payment_data = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.apple_pay_token_data"
        
        builder = (self.client.payments.create_payment("applepay")
                  .payment_data(payment_data)
                  .customer_card_name("Jane Smith")
                  .currency("EUR")
                  .amount_debit(99.99)
                  .invoice("ORDER-2025-001")
                  .description("Premium subscription"))
        
        payment_request = builder.build()
        result_dict = payment_request.to_dict()
        
        # Verify the complete structure matches Buckaroo API format
        expected_structure = {
            "Currency": "EUR",
            "AmountDebit": 99.99,
            "Invoice": "ORDER-2025-001",
            "Description": "Premium subscription",
            "Services": {
                "ServiceList": [
                    {
                        "Name": "applepay",
                        "Action": "Pay",
                        "Parameters": [
                            {
                                "Name": "PaymentData",
                                "Value": payment_data
                            },
                            {
                                "Name": "CustomerCardName",
                                "Value": "Jane Smith"
                            }
                        ]
                    }
                ]
            }
        }
        
        # Check key fields
        self.assertEqual(result_dict["Currency"], expected_structure["Currency"])
        self.assertEqual(result_dict["AmountDebit"], expected_structure["AmountDebit"])
        self.assertEqual(result_dict["Invoice"], expected_structure["Invoice"])
        
        # Check service structure
        service = result_dict["Services"]["ServiceList"][0]
        self.assertEqual(service["Name"], "applepay")
        self.assertEqual(service["Action"], "Pay")
        self.assertEqual(len(service["Parameters"]), 2)


if __name__ == '__main__':
    unittest.main()