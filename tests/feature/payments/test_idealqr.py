"""Feature test: idealqr pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestIdealqrFeature:
    def test_idealqr_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("idealqr")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("idealqr", TestHelpers.standard_payload(
            invoice="INV-IQRT-001",
            description="Test idealqr",
        )).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_idealqr_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("idealqr")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("idealqr", TestHelpers.standard_payload(
            invoice="INV-IQRR-001",
            description="Refund",
            original_transaction_key="some-key",
        )).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
