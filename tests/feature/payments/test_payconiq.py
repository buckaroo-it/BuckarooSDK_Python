"""Feature test: payconiq pay() and capability methods through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestPayconiqFeature:
    """Feature tests for Payconiq with InstantRefund and FastCheckout capabilities."""

    def test_payconiq_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("payconiq")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("payconiq", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test payconiq",
            "invoice": "INV-PCQ-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_payconiq_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("payconiq")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("payconiq", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Refund",
            "invoice": "INV-PCQ-REFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_payconiq_instant_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "payconiq", "Action": "InstantRefund", "Parameters": []}],
            "ServiceCode": "payconiq",
            "AmountCredit": 10.00,
            "AmountDebit": None,
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("payconiq", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Instant refund",
            "invoice": "INV-PCQ-IREFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_payconiq_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("payconiq", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("payconiq", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Fast checkout",
            "invoice": "INV-PCQ-FAST",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
