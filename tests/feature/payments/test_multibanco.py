from tests.support.helpers import Helpers


class TestMultibancoFeature:
    def test_multibanco_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="multibanco",
            invoice="INV-MB-001",
            payload_overrides={"description": "Test multibanco"},
        )
