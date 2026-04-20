"""Feature test: eps pay() round-trip through full stack with MockBuckaroo."""

from tests.support.test_helpers import TestHelpers


class TestEpsFeature:
    def test_eps_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="eps", invoice="INV-EPS-001",
            payload_overrides={"description": "Test eps"},
        )
