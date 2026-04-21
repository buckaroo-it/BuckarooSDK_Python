"""Feature test: payconiq pay() and capability methods through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestPayconiqFeature:
    """Feature tests for Payconiq with InstantRefund and FastCheckout capabilities."""

    def test_payconiq_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-001",
            payload_overrides={"description": "Test payconiq"},
        )

    def test_payconiq_refund(self, buckaroo, mock_strategy):
        Helpers.assert_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-REFUND",
        )

    def test_payconiq_instant_refund(self, buckaroo, mock_strategy):
        Helpers.assert_instant_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-IREFUND",
        )

    def test_payconiq_fast_checkout(self, buckaroo, mock_strategy):
        Helpers.assert_fast_checkout_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-FAST",
        )
