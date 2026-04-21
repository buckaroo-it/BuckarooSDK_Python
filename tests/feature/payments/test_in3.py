"""Feature test: in3 pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


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
                    {"description": "Widget", "quantity": "2", "price": "12.50"},
                ],
                "billingCustomer": [
                    {"firstName": "John", "lastName": "Doe"},
                ],
                "shippingCustomer": [
                    {"firstName": "John", "lastName": "Doe"},
                ],
            },
        )
