"""Feature test: klarna pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestKlarnaFeature:
    def test_klarna_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response(
            "klarna", overrides={"AmountDebit": 25.00}
        )
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("klarna", TestHelpers.standard_payload(
            invoice="INV-KLARNA-001",
            amount=25.00,
            description="Test klarna",
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
        assert response.currency == "EUR"
        assert response.amount_debit == 25.00
