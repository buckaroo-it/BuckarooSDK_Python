"""Feature tests for Google Pay payment method."""

from tests.support.helpers import Helpers


class TestGooglepayFeature:
    def test_googlepay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="googlepay",
            invoice="INV-GP-001",
            payload_overrides={"description": "Test googlepay"},
            service_params={"PaymentData": "eyJ0b2tlbiI6InRlc3QifQ=="},
        )
