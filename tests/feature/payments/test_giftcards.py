"""Feature test: giftcards pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_service_parameters
from tests.support.test_helpers import TestHelpers


class TestGiftcardsFeature:
    def test_giftcards_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        TestHelpers.assert_pay_returns_pending_with_redirect(
            buckaroo, mock_strategy,
            method="giftcards", invoice="INV-GC-001",
            payload_overrides={"description": "Test giftcards"},
            service_params={"Cardnumber": "1234567890123456", "PIN": "1234"},
        )

    def test_giftcards_pay_sends_cardnumber_and_pin_on_the_wire(
        self, recording_buckaroo, recording_mock
    ):
        """service_parameters dict must reach ServiceList[0].Parameters.

        The SDK capitalizes parameter names, so ``"PIN"`` becomes ``"Pin"``
        on the wire. Assert both the value pairing and the presence of both
        keys so a builder that silently drops service_parameters would fail.
        """
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                TestHelpers.pending_redirect_response("giftcards"),
            )
        )
        recording_buckaroo.payments.create_payment(
            "giftcards",
            TestHelpers.standard_payload(
                invoice="INV-GC-WIRE",
                service_parameters={"Cardnumber": "1234567890123456", "PIN": "1234"},
            ),
        ).pay()

        assert recorded_action(recording_mock) == "Pay"
        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(recording_mock)}
        assert params.get("Cardnumber") == "1234567890123456"
        assert params.get("Pin") == "1234"
