from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestPaypalFeature:
    def test_paypal_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("paypal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paypal", {
            "amount": 10.00, "currency": "EUR", "description": "Test paypal",
            "invoice": "INV-PP-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_paypal_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("paypal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paypal", {
            "amount": 10.00, "currency": "EUR", "description": "Refund",
            "invoice": "INV-PPR-001",
            "original_transaction_key": "some-key",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
