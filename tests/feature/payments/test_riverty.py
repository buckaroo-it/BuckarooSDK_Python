"""Feature test: riverty pay() round-trip through full stack with MockBuckaroo."""

from tests.support.test_helpers import TestHelpers


class TestRivertyFeature:
    def test_riverty_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="riverty", invoice="INV-RIV-001",
            payload_overrides={"amount": 25.00, "description": "Test riverty"},
            service_params={
                "article": [
                    {"description": "Widget", "quantity": "2", "price": "12.50"},
                ],
                "billingCustomer": {"firstName": "John", "lastName": "Doe"},
                "shippingCustomer": {"firstName": "John", "lastName": "Doe"},
            },
        )
