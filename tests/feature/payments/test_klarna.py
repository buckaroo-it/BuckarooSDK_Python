"""Feature test: klarna pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestKlarnaFeature:
    def test_klarna_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response = Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="klarna",
            invoice="INV-KLARNA-001",
            payload_overrides={"amount": 25.00, "description": "Test klarna"},
            service_params={
                "article": [
                    {"description": "Widget", "quantity": "2", "price": "12.50"},
                ],
                "billingCustomer": [{"firstName": "John", "lastName": "Doe"}],
                "shippingCustomer": [{"firstName": "John", "lastName": "Doe"}],
            },
        )
        assert response.currency == "EUR"
