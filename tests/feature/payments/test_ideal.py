from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action
from tests.support.helpers import Helpers


class TestIdealFeature:
    """Feature tests for iDEAL payment method with InstantRefund and FastCheckout capabilities."""

    def test_ideal_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="ideal",
            invoice="INV-IDEAL-001",
            payload_overrides={"description": "Test ideal"},
        )

    def test_ideal_case_insensitive_lookup(self, buckaroo, mock_strategy):
        response_body = Helpers.pending_redirect_response("ideal")
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        response = buckaroo.payments.create_payment(
            "IDEAL",
            Helpers.standard_payload(
                invoice="INV-CASE",
                description="Case test",
            ),
        ).pay()
        assert response.is_pending()
        assert response.key == response_body["Key"]

    def test_ideal_refund(self, buckaroo, mock_strategy):
        Helpers.assert_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="ideal",
            invoice="INV-REFUND",
        )

    def test_ideal_instant_refund(self, buckaroo, mock_strategy):
        Helpers.assert_instant_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="ideal",
            invoice="INV-IREFUND",
        )

    def test_ideal_fast_checkout(self, buckaroo, mock_strategy):
        Helpers.assert_fast_checkout_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="ideal",
            invoice="INV-FAST",
        )

    # ------------------------------------------------------------------
    # Wire-level assertions — verify BankTransferCapabilities mixins
    # (InstantRefund + FastCheckout) actually put the right Action on
    # the outgoing request.

    def test_ideal_instant_refund_sends_action_instantrefund_on_the_wire(
        self, recording_buckaroo, recording_mock
    ):
        """The InstantRefundCapable mixin must put ``Action=instantRefund`` on the wire."""
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                Helpers.success_response(
                    {
                        "Services": [
                            {"Name": "ideal", "Action": "InstantRefund", "Parameters": []}
                        ],
                        "ServiceCode": "ideal",
                        "AmountCredit": 10.00,
                        "AmountDebit": None,
                    }
                ),
            )
        )
        recording_buckaroo.payments.create_payment(
            "ideal",
            Helpers.standard_payload(
                invoice="INV-IDEAL-WIRE-IREFUND",
                original_transaction_key="ABC123",
            ),
        ).instantRefund()

        assert recorded_action(recording_mock) == "instantRefund"

    def test_ideal_fast_checkout_sends_action_payfastcheckout_on_the_wire(
        self, recording_buckaroo, recording_mock
    ):
        """The FastCheckoutCapable mixin must put ``Action=payFastCheckout`` on the wire."""
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                Helpers.pending_redirect_response("ideal", "PayFastCheckout"),
            )
        )
        recording_buckaroo.payments.create_payment(
            "ideal",
            Helpers.standard_payload(invoice="INV-IDEAL-WIRE-FAST"),
        ).payFastCheckout()

        assert recorded_action(recording_mock) == "payFastCheckout"
