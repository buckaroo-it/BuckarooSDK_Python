from tests.support.test_helpers import TestHelpers


class TestDefaultFeature:
    def test_default_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="default", invoice="INV-DEF-001",
            payload_overrides={"description": "Test default"},
        )
