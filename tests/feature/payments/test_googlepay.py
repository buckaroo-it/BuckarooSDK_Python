"""Feature tests for Google Pay payment method."""

from tests.support.test_helpers import TestHelpers


class TestGooglepayFeature:
    def test_googlepay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="googlepay", invoice="INV-GP-001",
            payload_overrides={"description": "Test googlepay"},
            service_params={"PaymentData": "eyJ0b2tlbiI6InRlc3QifQ=="},
        )
