from tests.support.helpers import Helpers


class TestSofortFeature:
    """Feature tests for Sofort payment method with InstantRefund and FastCheckout capabilities."""

    def test_sofort_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response = Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="sofort",
            invoice="INV-SOF-001",
            payload_overrides={"description": "Test sofort"},
        )
        assert response.currency == "EUR"
        assert response.amount_debit == 10.00

    def test_sofort_refund(self, buckaroo, mock_strategy):
        Helpers.assert_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="sofort",
            invoice="INV-SOF-REFUND",
        )

    def test_sofort_instant_refund(self, buckaroo, mock_strategy):
        Helpers.assert_instant_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="sofort",
            invoice="INV-SOF-IREFUND",
        )

    def test_sofort_fast_checkout(self, buckaroo, mock_strategy):
        Helpers.assert_fast_checkout_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="sofort",
            invoice="INV-SOF-FAST",
        )
