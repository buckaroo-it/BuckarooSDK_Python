from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestIdealFeature:
    """Feature tests for iDEAL payment method with InstantRefund and FastCheckout capabilities."""

    def test_ideal_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("ideal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("ideal", {
            "amount": 10.00, "currency": "EUR", "description": "Test ideal",
            "invoice": "INV-IDEAL-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_ideal_case_insensitive_lookup(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("ideal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("IDEAL", {
            "amount": 10.00, "currency": "EUR", "description": "Case test",
            "invoice": "INV-CASE",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()
        assert response.is_pending()
        assert response.key == response_body["Key"]

    def test_ideal_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("ideal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("ideal", {
            "amount": 10.00, "currency": "EUR", "description": "Refund",
            "invoice": "INV-REFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_ideal_instant_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "ideal", "Action": "InstantRefund", "Parameters": []}],
            "ServiceCode": "ideal",
            "AmountCredit": 10.00,
            "AmountDebit": None,
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("ideal", {
            "amount": 10.00, "currency": "EUR", "description": "Instant refund",
            "invoice": "INV-IREFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_ideal_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("ideal", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("ideal", {
            "amount": 10.00, "currency": "EUR", "description": "Fast checkout",
            "invoice": "INV-FAST",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
