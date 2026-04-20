from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestIdealFeature:
    """Feature tests for iDEAL payment method with InstantRefund and FastCheckout capabilities."""

    def test_ideal_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="ideal", invoice="INV-IDEAL-001",
            payload_overrides={"description": "Test ideal"},
        )

    def test_ideal_case_insensitive_lookup(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("ideal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("IDEAL", TestHelpers.standard_payload(
            invoice="INV-CASE",
            description="Case test",
        )).pay()
        assert response.is_pending()
        assert response.key == response_body["Key"]

    def test_ideal_refund(self, buckaroo, mock_strategy):
        response_body = TestHelpers.refund_response("ideal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
            invoice="INV-REFUND",
            description="Refund",
            original_transaction_key="ABC123",
        )).refund()
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
        response = buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
            invoice="INV-IREFUND",
            description="Instant refund",
            original_transaction_key="ABC123",
        )).instantRefund()
        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

    def test_ideal_fast_checkout(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response("ideal", "PayFastCheckout")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment("ideal", TestHelpers.standard_payload(
            invoice="INV-FAST",
            description="Fast checkout",
        )).payFastCheckout()
        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
