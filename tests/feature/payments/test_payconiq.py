"""Feature test: payconiq pay() and capability methods through full stack with MockBuckaroo."""

import pytest

from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_request
from tests.support.helpers import Helpers


class TestPayconiqFeature:
    """Feature tests for Payconiq with InstantRefund and FastCheckout capabilities."""

    def test_payconiq_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-001",
            payload_overrides={"description": "Test payconiq"},
        )

    def test_payconiq_refund(self, buckaroo, mock_strategy):
        Helpers.assert_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-REFUND",
        )

    def test_payconiq_instant_refund(self, buckaroo, mock_strategy):
        Helpers.assert_instant_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-IREFUND",
        )

    def test_payconiq_fast_checkout(self, buckaroo, mock_strategy):
        Helpers.assert_fast_checkout_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="payconiq",
            invoice="INV-PCQ-FAST",
        )

    # ------------------------------------------------------------------
    # Wire-level assertions — verify BankTransferCapabilities' InstantRefund
    # mixin puts the right Action, OriginalTransactionKey and AmountCredit
    # on the outgoing request for Payconiq (partial + full).

    def test_payconiq_instant_refund_full_sends_action_instantrefund_on_the_wire(
        self, recording_buckaroo, recording_mock
    ):
        """Full refund (``refund_amount`` omitted): AmountDebit swaps to AmountCredit."""
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                Helpers.success_response(
                    {
                        "Services": [
                            {"Name": "payconiq", "Action": "InstantRefund", "Parameters": []}
                        ],
                        "ServiceCode": "payconiq",
                        "AmountCredit": 10.00,
                        "AmountDebit": None,
                    }
                ),
            )
        )
        recording_buckaroo.payments.create_payment(
            "payconiq",
            Helpers.standard_payload(
                invoice="INV-PCQ-WIRE-IREFUND-FULL",
                original_transaction_key="ABC123",
            ),
        ).instantRefund()

        assert recorded_action(recording_mock) == "instantRefund"
        request = recorded_request(recording_mock)
        assert request["Services"]["ServiceList"][0]["Name"] == "payconiq"
        assert request["OriginalTransactionKey"] == "ABC123"
        assert request["AmountCredit"] == 10.00
        assert "AmountDebit" not in request

    def test_payconiq_instant_refund_partial_sends_refund_amount_as_credit(
        self, recording_buckaroo, recording_mock
    ):
        """Partial refund (``refund_amount`` in payload): AmountCredit is that amount."""
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                Helpers.success_response(
                    {
                        "Services": [
                            {"Name": "payconiq", "Action": "InstantRefund", "Parameters": []}
                        ],
                        "ServiceCode": "payconiq",
                        "AmountCredit": 4.00,
                        "AmountDebit": None,
                    }
                ),
            )
        )
        recording_buckaroo.payments.create_payment(
            "payconiq",
            Helpers.standard_payload(
                invoice="INV-PCQ-WIRE-IREFUND-PARTIAL",
                original_transaction_key="ABC123",
                refund_amount=4.00,
            ),
        ).instantRefund()

        assert recorded_action(recording_mock) == "instantRefund"
        request = recorded_request(recording_mock)
        assert request["Services"]["ServiceList"][0]["Name"] == "payconiq"
        assert request["OriginalTransactionKey"] == "ABC123"
        assert request["AmountCredit"] == 4.00
        assert "AmountDebit" not in request

    def test_payconiq_instant_refund_raises_without_original_transaction_key(
        self, recording_buckaroo
    ):
        """A missing ``original_transaction_key`` must fail fast, matching iDEAL."""
        with pytest.raises(ValueError, match="Original transaction key is required"):
            recording_buckaroo.payments.create_payment(
                "payconiq",
                Helpers.standard_payload(invoice="INV-PCQ-WIRE-IREFUND-NOKEY"),
            ).instantRefund()

    def test_payconiq_instant_refund_surfaces_api_rejection_as_failed_response(
        self, buckaroo, mock_strategy
    ):
        """A rejected instant refund is surfaced as a standard failed response,
        not an exception."""
        response_body = Helpers.failed_response(
            "Refund rejected",
            overrides={
                "Services": [{"Name": "payconiq", "Action": "InstantRefund", "Parameters": []}],
                "ServiceCode": "payconiq",
                "AmountCredit": None,
                "AmountDebit": 10.00,
            },
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))
        payload = Helpers.standard_payload(
            invoice="INV-PCQ-IREFUND-REJECTED",
            original_transaction_key="ABC123",
        )
        response = buckaroo.payments.create_payment("payconiq", payload).instantRefund()

        assert response.is_failed()
        assert not response.is_successful()
        assert response.key == response_body["Key"]
