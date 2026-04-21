"""Smoke test verifying feature test fixtures work end-to-end."""

from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestFeatureFixturesSmoke:
    """Verify conftest fixtures wire up correctly."""

    def test_buckaroo_fixture_creates_payment_builder(self, buckaroo, mock_strategy):
        """buckaroo.payments.create_payment returns a builder."""
        builder = buckaroo.payments.create_payment(
            "ideal",
            {
                "amount": 10.00,
                "currency": "EUR",
                "description": "Smoke test",
                "invoice": "SMOKE-001",
            },
        )
        assert isinstance(builder, PaymentBuilder)

    def test_mock_strategy_intercepts_pay_call(self, buckaroo, mock_strategy):
        """Queued mock is consumed by builder.pay()."""
        response_body = Helpers.success_response(
            {
                "Services": [{"Name": "ideal", "Action": "Pay", "Parameters": []}],
                "ServiceCode": "ideal",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        builder = buckaroo.payments.create_payment(
            "ideal",
            Helpers.standard_payload(
                invoice="SMOKE-001",
                description="Smoke test",
            ),
        )
        result = builder.pay()
        assert result.key == response_body["Key"]

    def test_pending_redirect_response_helper(self):
        """pending_redirect_response builds a valid Buckaroo response shape."""
        resp = Helpers.pending_redirect_response("ideal")
        assert resp["Status"]["Code"]["Code"] == 791
        assert resp["RequiredAction"]["Name"] == "Redirect"
        assert resp["ServiceCode"] == "ideal"
        assert resp["Services"][0]["Name"] == "ideal"

    def test_refund_response_helper(self):
        """refund_response builds a valid Buckaroo refund shape."""
        resp = Helpers.refund_response("ideal")
        assert resp["Services"][0]["Action"] == "Refund"
        assert resp["AmountCredit"] == 10.00
        assert resp["ServiceCode"] == "ideal"
