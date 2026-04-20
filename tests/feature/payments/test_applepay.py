"""Feature tests for Apple Pay payment method."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestApplepayFeature:
    def test_applepay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("applepay")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("applepay", TestHelpers.standard_payload(
            invoice="INV-APPLEPAY-001",
            description="Test applepay payment",
            service_parameters={
                "PaymentData": "eyJ0b2tlbiI6InRlc3QifQ==",
            },
        )).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
