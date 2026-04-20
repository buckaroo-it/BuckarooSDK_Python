from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestTwintFeature:
    def test_twint_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("twint")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        response = buckaroo.payments.create_payment("twint", TestHelpers.standard_payload(
            invoice="INV-TWI-001",
            description="Test twint",
        )).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
