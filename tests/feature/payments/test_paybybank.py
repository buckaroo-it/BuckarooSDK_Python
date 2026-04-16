"""Feature test: paybybank pay() and capability methods through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestPaybybankFeature:
    """Feature tests for PayByBank with InstantRefund and FastCheckout capabilities."""

    def test_paybybank_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("paybybank")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paybybank", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Test paybybank",
            "invoice": "INV-PBB-001",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
            "service_parameters": {"issuer": "INGBNL2A"},
        }).pay()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]

    def test_paybybank_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("paybybank")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paybybank", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Refund",
            "invoice": "INV-PBB-REFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).refund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_paybybank_instant_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.success_response({
            "Services": [{"Name": "paybybank", "Action": "InstantRefund", "Parameters": []}],
            "ServiceCode": "paybybank",
            "AmountCredit": 10.00,
            "AmountDebit": None,
        })
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paybybank", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Instant refund",
            "invoice": "INV-PBB-IREFUND",
            "original_transaction_key": "ABC123",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_paybybank_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("paybybank", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("paybybank", {
            "amount": 10.00,
            "currency": "EUR",
            "description": "Fast checkout",
            "invoice": "INV-PBB-FAST",
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        }).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
