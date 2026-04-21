"""Feature test: bizum pay() round-trip through full stack with MockBuckaroo."""

from tests.support.helpers import Helpers


class TestBizumFeature:
    def test_bizum_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="bizum",
            invoice="INV-BIZUM-001",
            payload_overrides={"description": "Test bizum"},
        )
