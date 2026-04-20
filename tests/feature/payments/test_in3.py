"""Feature test: in3 pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestIn3Feature:
    def test_in3_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("in3")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("in3", TestHelpers.standard_payload(
            invoice="INV-IN3-001",
            amount=25.00,
            description="Test in3",
            service_parameters={
                "article": [
                    {"description": "Widget", "quantity": "2", "price": "12.50"},
                ],
                "billingCustomer": [
                    {"firstName": "John", "lastName": "Doe"},
                ],
                "shippingCustomer": [
                    {"firstName": "John", "lastName": "Doe"},
                ],
            },
        )).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
