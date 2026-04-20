"""Feature tests for Billink payment method."""

from tests.support.test_helpers import TestHelpers


class TestBillinkFeature:
    def test_billink_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="billink", invoice="INV-BILLINK-001",
            payload_overrides={"description": "Test billink"},
            service_params={
                "billingCustomer": [
                    {"firstName": "John", "lastName": "Doe", "email": "john@example.com"},
                ],
                "shippingCustomer": [{"firstName": "John", "lastName": "Doe"}],
                "article": [
                    {"description": "Widget", "quantity": "1", "price": "10.00"},
                ],
            },
        )
