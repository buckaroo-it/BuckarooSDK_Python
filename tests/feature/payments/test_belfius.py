"""Feature test: belfius pay() round-trip through full stack with MockBuckaroo."""

from tests.support.test_helpers import TestHelpers


class TestBelfiusFeature:
    def test_belfius_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy, method="belfius", invoice="INV-001"
        )
