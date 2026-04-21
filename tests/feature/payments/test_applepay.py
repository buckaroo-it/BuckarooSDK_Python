"""Feature tests for Apple Pay payment method."""

from tests.support.helpers import Helpers


class TestApplepayFeature:
    def test_applepay_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="applepay",
            invoice="INV-APPLEPAY-001",
            payload_overrides={"description": "Test applepay payment"},
            service_params={"PaymentData": "eyJ0b2tlbiI6InRlc3QifQ=="},
        )
