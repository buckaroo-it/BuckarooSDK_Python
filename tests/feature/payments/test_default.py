from tests.support.helpers import Helpers


class TestDefaultFeature:
    def test_default_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="default",
            invoice="INV-DEF-001",
            payload_overrides={"description": "Test default"},
        )
