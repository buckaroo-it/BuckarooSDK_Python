"""Feature test: paybybank pay() and capability methods through full stack with MockBuckaroo."""

from tests.support.test_helpers import TestHelpers


class TestPaybybankFeature:
    """Feature tests for PayByBank with InstantRefund and FastCheckout capabilities."""

    def test_paybybank_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="paybybank", invoice="INV-PBB-001",
            payload_overrides={"description": "Test paybybank"},
            service_params={"issuer": "INGBNL2A"},
        )

    def test_paybybank_refund(self, buckaroo, mock_strategy):
        TestHelpers.assert_refund_returns_success(
            buckaroo, mock_strategy, method="paybybank", invoice="INV-PBB-REFUND",
        )

    def test_paybybank_instant_refund(self, buckaroo, mock_strategy):
        TestHelpers.assert_instant_refund_returns_success(
            buckaroo, mock_strategy, method="paybybank", invoice="INV-PBB-IREFUND",
        )

    def test_paybybank_fast_checkout(self, buckaroo, mock_strategy):
        TestHelpers.assert_fast_checkout_returns_pending_with_redirect(
            buckaroo, mock_strategy, method="paybybank", invoice="INV-PBB-FAST",
        )
