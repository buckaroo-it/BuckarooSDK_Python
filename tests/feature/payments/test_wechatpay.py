"""Feature test: wechatpay pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestWechatpayFeature:
    def test_wechatpay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("wechatpay")
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("wechatpay", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test wechatpay",
            "invoice": "INV-WCP-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
