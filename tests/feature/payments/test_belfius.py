"""Feature test: belfius pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestBelfiusFeature:
    def test_belfius_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy, method="belfius", invoice="INV-001"
        )
