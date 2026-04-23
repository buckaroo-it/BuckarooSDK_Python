"""Feature test: paybybank pay() and capability methods through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_service_parameters
from tests.support.helpers import Helpers


class TestPaybybankFeature:
    """Feature tests for PayByBank with InstantRefund and FastCheckout capabilities."""

    def test_paybybank_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="paybybank",
            invoice="INV-PBB-001",
            payload_overrides={"description": "Test paybybank"},
            service_params={"issuer": "INGBNL2A"},
        )

    def test_paybybank_pay_sends_issuer_on_the_wire(self, recording_buckaroo, recording_mock):
        """service_parameters['issuer'] must reach ServiceList[0].Parameters."""
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                Helpers.pending_redirect_response("paybybank"),
            )
        )
        recording_buckaroo.payments.create_payment(
            "paybybank",
            Helpers.standard_payload(
                invoice="INV-PBB-WIRE",
                service_parameters={"issuer": "INGBNL2A"},
            ),
        ).pay()

        assert recorded_action(recording_mock) == "Pay"
        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(recording_mock)}
        assert params.get("Issuer") == "INGBNL2A"

    def test_paybybank_refund(self, buckaroo, mock_strategy):
        Helpers.assert_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="paybybank",
            invoice="INV-PBB-REFUND",
        )

    def test_paybybank_instant_refund(self, buckaroo, mock_strategy):
        Helpers.assert_instant_refund_returns_success(
            buckaroo,
            mock_strategy,
            method="paybybank",
            invoice="INV-PBB-IREFUND",
        )

    def test_paybybank_fast_checkout(self, buckaroo, mock_strategy):
        Helpers.assert_fast_checkout_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="paybybank",
            invoice="INV-PBB-FAST",
        )
