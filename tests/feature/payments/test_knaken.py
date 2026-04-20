"""Feature test: knaken pay() round-trip through full stack with MockBuckaroo."""

from tests.support.test_helpers import TestHelpers


class TestKnakenFeature:
    def test_knaken_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="knaken", invoice="INV-KNK-001",
            payload_overrides={"description": "Test knaken"},
        )
