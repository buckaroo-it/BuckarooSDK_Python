import unittest
from datetime import date, datetime
from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.idealqr_payment_builder import IdealQrPaymentBuilder
from buckaroo.models.payment_request import Parameter


class TestIdealQrPaymentBuilder(unittest.TestCase):
    """Test suite for IdealQr payment builder."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = BuckarooClient("test_store_key", "test_secret_key")

    def test_create_idealqr_payment_builder(self):
        """Test creating an IdealQr payment builder."""
        builder = self.client.payments.create_payment("idealqr")
        self.assertIsInstance(builder, IdealQrPaymentBuilder)

    def test_idealqr_service_name_and_action(self):
        """Test IdealQr service name and action."""
        builder = self.client.payments.create_payment("idealqr")
        self.assertEqual(builder.get_service_name(), "IdealQr")
        self.assertEqual(builder.get_action(), "Generate")

    def test_add_qr_parameter(self):
        """Test adding QR-specific parameters."""
        builder = self.client.payments.create_payment("idealqr")
        builder.add_qr_parameter("TestParam", "TestValue", "TestGroup", "TestID")
        
        self.assertEqual(len(builder._parameters), 1)
        param = builder._parameters[0]
        self.assertEqual(param.name, "TestParam")
        self.assertEqual(param.value, "TestValue")
        self.assertEqual(param.group_type, "TestGroup")
        self.assertEqual(param.group_id, "TestID")

    def test_idealqr_fluent_interface(self):
        """Test IdealQr fluent interface methods."""
        builder = (self.client.payments.create_payment("idealqr")
                  .description("Test purchase")
                  .min_amount(0.10)
                  .max_amount(10.0)
                  .image_size(2000)
                  .purchase_id("Testpurchase123")
                  .is_one_off(False)
                  .amount(1.00)
                  .amount_is_changeable(True)
                  .expiration("2018-09-30")
                  .is_processing(False))
        
        # Verify parameters were added
        param_names = [param.name for param in builder._parameters]
        expected_params = [
            "Description", "MinAmount", "MaxAmount", "ImageSize",
            "PurchaseId", "IsOneOff", "Amount", "AmountIsChangeable",
            "Expiration", "IsProcessing"
        ]
        
        for expected_param in expected_params:
            self.assertIn(expected_param, param_names)

    def test_idealqr_from_dict(self):
        """Test creating IdealQr payment from dictionary."""
        params = {
            'qr_description': 'Test purchase',
            'min_amount': 0.10,
            'max_amount': 10.0,
            'image_size': 2000,
            'purchase_id': 'Testpurchase123',
            'is_one_off': False,
            'amount': 1.00,
            'amount_is_changeable': True,
            'expiration': '2018-09-30',
            'is_processing': False
        }
        
        builder = self.client.payments.create_payment("idealqr", params)
        
        # Verify parameters were set
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["Description"], "Test purchase")
        self.assertEqual(param_dict["MinAmount"], "0.1")
        self.assertEqual(param_dict["MaxAmount"], "10.0")
        self.assertEqual(param_dict["ImageSize"], "2000")
        self.assertEqual(param_dict["PurchaseId"], "Testpurchase123")
        self.assertEqual(param_dict["IsOneOff"], "false")
        self.assertEqual(param_dict["Amount"], "1.0")
        self.assertEqual(param_dict["AmountIsChangeable"], "true")
        self.assertEqual(param_dict["Expiration"], "2018-09-30")
        self.assertEqual(param_dict["IsProcessing"], "false")

    def test_idealqr_expiration_with_date_object(self):
        """Test setting expiration with date object."""
        builder = self.client.payments.create_payment("idealqr")
        test_date = date(2024, 12, 31)
        builder.expiration(test_date)
        
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["Expiration"], "2024-12-31")

    def test_idealqr_expiration_with_datetime_object(self):
        """Test setting expiration with datetime object."""
        builder = self.client.payments.create_payment("idealqr")
        test_datetime = datetime(2024, 12, 31, 15, 30, 45)
        builder.expiration(test_datetime)
        
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["Expiration"], "2024-12-31")

    def test_idealqr_build_complete_request(self):
        """Test building a complete IdealQr request."""
        builder = (self.client.payments.create_payment("idealqr")
                  .description("Test purchase")
                  .purchase_id("Testpurchase123")
                  .amount(1.00))
        
        payment_request = builder.build()
        
        # Check service structure
        self.assertEqual(len(payment_request.services.services), 1)
        service = payment_request.services.services[0]
        self.assertEqual(service.name, "IdealQr")
        self.assertEqual(service.action, "Generate")
        self.assertIsInstance(service.parameters, list)
        self.assertEqual(len(service.parameters), 3)

    def test_idealqr_to_dict_matches_expected_format(self):
        """Test that IdealQr generates the expected JSON format."""
        builder = (self.client.payments.create_payment("idealqr")
                  .description("Test purchase")
                  .min_amount(0.10)
                  .max_amount(10.0)
                  .image_size(2000)
                  .purchase_id("Testpurchase123")
                  .is_one_off(False)
                  .amount(1.00)
                  .amount_is_changeable(True)
                  .expiration("2018-09-30")
                  .is_processing(False))
        
        payment_request = builder.build()
        result_dict = payment_request.to_dict()
        
        # Check the Services structure
        self.assertIn("Services", result_dict)
        services = result_dict["Services"]
        self.assertIn("ServiceList", services)
        
        service_list = services["ServiceList"]
        self.assertEqual(len(service_list), 1)
        
        service = service_list[0]
        self.assertEqual(service["Name"], "IdealQr")
        self.assertEqual(service["Action"], "Generate")
        self.assertIn("Parameters", service)
        
        # Check parameters structure
        parameters = service["Parameters"]
        self.assertEqual(len(parameters), 10)
        
        # Verify parameter structure
        param_names = [param["Name"] for param in parameters]
        expected_params = [
            "Description", "MinAmount", "MaxAmount", "ImageSize",
            "PurchaseId", "IsOneOff", "Amount", "AmountIsChangeable",
            "Expiration", "IsProcessing"
        ]
        
        for expected_param in expected_params:
            self.assertIn(expected_param, param_names)
        
        # Check specific parameter format
        description_param = next(p for p in parameters if p["Name"] == "Description")
        self.assertEqual(description_param["Value"], "Test purchase")
        self.assertEqual(description_param["GroupType"], "")
        self.assertEqual(description_param["GroupID"], "")

    def test_idealqr_validation_missing_required_fields(self):
        """Test validation with missing required fields."""
        builder = self.client.payments.create_payment("idealqr")
        
        with self.assertRaises(ValueError) as context:
            builder.build()
        
        self.assertIn("Missing required QR parameters", str(context.exception))

    def test_idealqr_validation_with_required_fields(self):
        """Test validation passes with required fields."""
        builder = (self.client.payments.create_payment("idealqr")
                  .description("Test")
                  .purchase_id("Test123")
                  .amount(1.00))
        
        # Should not raise validation error
        payment_request = builder.build()
        self.assertIsNotNone(payment_request)

    def test_idealqr_execute(self):
        """Test executing IdealQr payment."""
        builder = (self.client.payments.create_payment("idealqr")
                  .description("Test purchase")
                  .purchase_id("Testpurchase123")
                  .amount(1.00))
        
        result = builder.execute()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("payment_request", result)

    def test_idealqr_boolean_parameters(self):
        """Test boolean parameter conversion."""
        builder = (self.client.payments.create_payment("idealqr")
                  .is_one_off(True)
                  .amount_is_changeable(False)
                  .is_processing(True))
        
        param_dict = {param.name: param.value for param in builder._parameters}
        self.assertEqual(param_dict["IsOneOff"], "true")
        self.assertEqual(param_dict["AmountIsChangeable"], "false")
        self.assertEqual(param_dict["IsProcessing"], "true")

    def test_idealqr_combined_dictionary_and_fluent(self):
        """Test combining dictionary and fluent interface for IdealQr."""
        params = {
            'qr_description': 'Initial description',
            'purchase_id': 'DICT123',
            'amount': 5.00
        }
        
        builder = (self.client.payments.create_payment("idealqr", params)
                  .description("Override description")  # Override
                  .min_amount(1.00)  # Add new parameter
                  .max_amount(20.00))  # Add new parameter
        
        param_dict = {param.name: param.value for param in builder._parameters}
        
        # Should have overridden description but kept other dict values
        self.assertEqual(param_dict["Description"], "Override description")
        self.assertEqual(param_dict["PurchaseId"], "DICT123")
        self.assertEqual(param_dict["Amount"], "5.0")
        self.assertEqual(param_dict["MinAmount"], "1.0")
        self.assertEqual(param_dict["MaxAmount"], "20.0")


class TestIdealQrParameterModel(unittest.TestCase):
    """Test suite for Parameter model."""

    def test_parameter_creation(self):
        """Test creating a Parameter object."""
        param = Parameter(
            name="TestName",
            value="TestValue",
            group_type="TestGroup",
            group_id="TestID"
        )
        
        self.assertEqual(param.name, "TestName")
        self.assertEqual(param.value, "TestValue")
        self.assertEqual(param.group_type, "TestGroup")
        self.assertEqual(param.group_id, "TestID")

    def test_parameter_to_dict(self):
        """Test Parameter to_dict method."""
        param = Parameter(
            name="Description",
            value="Test purchase",
            group_type="",
            group_id=""
        )
        
        expected_dict = {
            "Name": "Description",
            "GroupType": "",
            "GroupID": "",
            "Value": "Test purchase"
        }
        
        self.assertEqual(param.to_dict(), expected_dict)

    def test_parameter_defaults(self):
        """Test Parameter default values."""
        param = Parameter(name="TestName", value="TestValue")
        
        self.assertEqual(param.group_type, "")
        self.assertEqual(param.group_id, "")


if __name__ == '__main__':
    unittest.main()