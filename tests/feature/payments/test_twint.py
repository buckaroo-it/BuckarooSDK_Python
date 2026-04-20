from tests.support.test_helpers import TestHelpers


class TestTwintFeature:
    def test_twint_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="twint", invoice="INV-TWI-001",
            payload_overrides={"description": "Test twint"},
        )
