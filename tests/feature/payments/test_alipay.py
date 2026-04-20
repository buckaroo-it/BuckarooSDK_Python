"""Feature test: alipay pay() round-trip through full stack with MockBuckaroo."""

from tests.support.test_helpers import TestHelpers


class TestAlipayFeature:
    def test_alipay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response = TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="alipay", invoice="INV-ALIPAY-001",
            payload_overrides={"description": "Test alipay payment"},
            service_params={"UseMobileView": False},
        )
        assert response.currency == "EUR"
        assert response.amount_debit == 10.00
