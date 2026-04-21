"""Feature tests for Przelewy24 payment method."""

from tests.support.helpers import Helpers


class TestPrzelewy24Feature:
    def test_przelewy24_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="przelewy24",
            invoice="INV-P24-001",
            payload_overrides={"description": "Test przelewy24"},
            service_params={
                "customerEmail": "test@example.com",
                "customerFirstName": "John",
                "customerLastName": "Doe",
            },
        )
