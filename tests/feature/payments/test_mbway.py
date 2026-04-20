from tests.support.test_helpers import TestHelpers


class TestMbwayFeature:
    """Feature tests for MB WAY payment method."""

    def test_mbway_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="mbway", invoice="INV-MBW-001",
            payload_overrides={"description": "Test mbway"},
        )
