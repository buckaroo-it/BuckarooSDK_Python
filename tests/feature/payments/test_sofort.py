from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestSofortFeature:
    """Feature tests for Sofort payment method with InstantRefund and FastCheckout capabilities."""

    def test_sofort_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("sofort")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sofort", {
            "amount": 10.00, "currency": "EUR", "description": "Test sofort",
            "invoice": "INV-SOF-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        assert response.currency == "EUR"
        assert response.amount_debit == 10.00

    def test_sofort_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("sofort")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sofort", {
            "amount": 10.00, "currency": "EUR", "description": "Refund",
            "invoice": "INV-SOF-REFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_sofort_instant_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "sofort", "Action": "InstantRefund", "Parameters": []}],
            "ServiceCode": "sofort",
            "AmountCredit": 10.00,
            "AmountDebit": None,
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sofort", {
            "amount": 10.00, "currency": "EUR", "description": "Instant refund",
            "invoice": "INV-SOF-IREFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_sofort_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("sofort", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sofort", {
            "amount": 10.00, "currency": "EUR", "description": "Fast checkout",
            "invoice": "INV-SOF-FAST",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
