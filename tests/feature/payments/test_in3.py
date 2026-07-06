"""Feature test: in3 pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_service_parameters


class TestIn3Feature:
    def test_in3_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="in3",
            invoice="INV-IN3-001",
            payload_overrides={"amount": 25.00, "description": "Test in3"},
            service_params={
                "article": [
                    {"description": "Widget", "quantity": "2", "GrossUnitPrice": "12.50"},
                ],
                "billingCustomer": [
                    {"firstName": "John", "lastName": "Doe"},
                ],
                "shippingCustomer": [
                    {"firstName": "John", "lastName": "Doe"},
                ],
            },
        )

    def test_in3_authorize_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        def add_service_params(builder):
            builder.add_parameter("route", "AbnB2b")
            builder.add_parameter(
                "article", [{"description": "Widget", "quantity": "2", "GrossUnitPrice": "12.50"}]
            )
            builder.add_parameter("billingCustomer", [{"firstName": "John", "lastName": "Doe"}])
            builder.add_parameter("shippingCustomer", [{"firstName": "John", "lastName": "Doe"}])

        Helpers.assert_action_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="in3",
            invoice="INV-IN3-002",
            action_name="Authorize",
            call_method="authorize",
            payload_overrides={"amount": 25.00, "description": "Test in3 authorize"},
            extra_builder_setup=add_service_params,
        )

    def test_in3_authorize_then_capture_round_trip(self, buckaroo, mock_strategy):
        auth_response_body = Helpers.pending_redirect_response("in3", "Authorize")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", auth_response_body)
        )

        builder = buckaroo.payments.create_payment(
            "in3",
            Helpers.standard_payload(
                invoice="INV-IN3-003", amount=25.00, description="Test in3 authorize"
            ),
        )
        builder.add_parameter("route", "AbnB2b")
        builder.add_parameter(
            "article", [{"description": "Widget", "quantity": "2", "GrossUnitPrice": "12.50"}]
        )
        builder.add_parameter("billingCustomer", [{"firstName": "John", "lastName": "Doe"}])
        builder.add_parameter("shippingCustomer", [{"firstName": "John", "lastName": "Doe"}])
        authorize_response = builder.authorize()
        assert authorize_response.is_pending()

        capture_response_body = Helpers.success_response(
            {
                "Services": [{"Name": "in3", "Action": "Capture", "Parameters": []}],
                "ServiceCode": "in3",
            }
        )
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", capture_response_body)
        )
        capture_response = builder.capture(
            original_transaction_key=authorize_response.key, amount=25.00
        )

        assert capture_response.status.code.code == 190
        assert capture_response.key == capture_response_body["Key"]

    def test_in3_authorize_with_business_customer_returns_pending_with_redirect(
        self, buckaroo, mock_strategy
    ):
        """ABN-AMRO "Zakelijk op rekening" (business-on-account) runs through the
        In3 Authorize action with route="AbnB2b". The business customer is marked
        by Category=B2B/CompanyName/CocNumber inside billingCustomer; those
        sub-fields flow through the existing billingCustomer list group.
        """

        def add_service_params(builder):
            builder.add_parameter("route", "AbnB2b")
            builder.add_parameter(
                "article", [{"description": "Widget", "quantity": "2", "GrossUnitPrice": "12.50"}]
            )
            builder.add_parameter(
                "billingCustomer",
                [
                    {
                        "Category": "B2B",
                        "CompanyName": "Acme B.V.",
                        "CocNumber": "12345678",
                        "firstName": "John",
                        "lastName": "Doe",
                    }
                ],
            )
            builder.add_parameter("shippingCustomer", [{"firstName": "John", "lastName": "Doe"}])

        Helpers.assert_action_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="in3",
            invoice="INV-IN3-004",
            action_name="Authorize",
            call_method="authorize",
            payload_overrides={"amount": 25.00, "description": "Test in3 authorize B2B"},
            extra_builder_setup=add_service_params,
        )

        billing_params = {
            param["Name"]: param["Value"]
            for param in recorded_service_parameters(mock_strategy)
            if param["GroupType"] == "Billingcustomer"
        }
        assert billing_params["Category"] == "B2B"
        assert billing_params["Companyname"] == "Acme B.V."
        assert billing_params["Cocnumber"] == "12345678"
