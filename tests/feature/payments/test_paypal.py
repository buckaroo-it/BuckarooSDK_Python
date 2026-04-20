from tests.support.test_helpers import TestHelpers


class TestPaypalFeature:
    def test_paypal_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="paypal", invoice="INV-PP-001",
            payload_overrides={"description": "Test paypal"},
        )

    def test_paypal_refund(self, buckaroo, mock_strategy):
        TestHelpers.assert_refund_returns_success(
            buckaroo, mock_strategy,
            method="paypal", invoice="INV-PPR-001",
            original_transaction_key="some-key",
            payload_overrides={"description": "Refund"},
        )
