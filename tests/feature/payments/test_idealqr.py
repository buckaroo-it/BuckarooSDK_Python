"""Feature test: idealqr pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestIdealqrFeature:
    def test_idealqr_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="idealqr",
            invoice="INV-IQRT-001",
            payload_overrides={"description": "Test idealqr"},
        )

    def test_idealqr_refund(self, buckaroo, mock_strategy):
        Helpers.assert_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="idealqr",
            invoice="INV-IQRR-001",
            original_transaction_key="some-key",
        )
