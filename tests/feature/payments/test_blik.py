"""Feature tests for Blik payment method."""

from tests.support.test_helpers import TestHelpers


class TestBlikFeature:
    def test_blik_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="blik", invoice="INV-BLIK-001",
            payload_overrides={"description": "Test blik"},
        )
