"""Feature tests for Swish payment method."""

from tests.support.helpers import Helpers


class TestSwishFeature:
    def test_swish_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="swish",
            invoice="INV-SWI-001",
            payload_overrides={"description": "Test swish"},
        )
