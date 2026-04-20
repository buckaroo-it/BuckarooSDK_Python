from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestSofortFeature:
    """Feature tests for Sofort payment method with InstantRefund and FastCheckout capabilities."""

    def test_sofort_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response = TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="sofort", invoice="INV-SOF-001",
            payload_overrides={"description": "Test sofort"},
        )
        assert response.currency == "EUR"
        assert response.amount_debit == 10.00

    def test_sofort_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("sofort")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sofort", TestHelpers.standard_payload(
            invoice="INV-SOF-REFUND",
            description="Refund",
            original_transaction_key="ABC123",
        )).refund()
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
        response = buckaroo.payments.create_payment("sofort", TestHelpers.standard_payload(
            invoice="INV-SOF-IREFUND",
            description="Instant refund",
            original_transaction_key="ABC123",
        )).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_sofort_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("sofort", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("sofort", TestHelpers.standard_payload(
            invoice="INV-SOF-FAST",
            description="Fast checkout",
        )).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
