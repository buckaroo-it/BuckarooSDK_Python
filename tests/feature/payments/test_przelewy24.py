"""Feature tests for Przelewy24 payment method."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestPrzelewy24Feature:
    def test_przelewy24_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("przelewy24")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("przelewy24", TestHelpers.standard_payload(
            invoice="INV-P24-001",
            description="Test przelewy24",
            service_parameters={
                "customerEmail": "test@example.com",
                "customerFirstName": "John",
                "customerLastName": "Doe",
            },
        )).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
