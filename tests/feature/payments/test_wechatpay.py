"""Feature test: wechatpay pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestWechatpayFeature:
    def test_wechatpay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="wechatpay",
            invoice="INV-WCP-001",
            payload_overrides={"description": "Test wechatpay"},
        )
