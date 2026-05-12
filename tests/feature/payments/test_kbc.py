"""Feature test: kbc pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestKbcFeature:
    def test_kbc_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="kbc",
            invoice="INV-KBC-001",
            payload_overrides={"description": "Test kbc"},
        )
