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
        TestHelpers.assert_refund_returns_success(
            buckaroo, mock_strategy, method="ideal", invoice="INV-REFUND",
        )

    def test_ideal_instant_refund(self, buckaroo, mock_strategy):
        TestHelpers.assert_instant_refund_returns_success(
            buckaroo, mock_strategy, method="ideal", invoice="INV-IREFUND",
        )

    def test_ideal_fast_checkout(self, buckaroo, mock_strategy):
        TestHelpers.assert_fast_checkout_returns_pending_with_redirect(
            buckaroo, mock_strategy, method="ideal", invoice="INV-FAST",
        )
