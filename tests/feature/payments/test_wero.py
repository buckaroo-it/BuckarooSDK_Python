from tests.support.test_helpers import TestHelpers


class TestWeroFeature:
    """Feature tests for Wero payment method."""

    def test_wero_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="wero", invoice="INV-WER-001",
            payload_overrides={"description": "Test wero"},
        )
