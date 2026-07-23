"""Feature test: giftcards pay() round-trip through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_service_parameters
from tests.support.helpers import Helpers


class TestGiftcardsFeature:
    def test_giftcards_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        Helpers.assert_pay_returns_pending_with_redirect(
            buckaroo,
            mock_strategy,
            method="giftcards",
            invoice="INV-GC-001",
            payload_overrides={"description": "Test giftcards", "giftcard_name": "other"},
            service_params={"Cardnumber": "1234567890123456", "PIN": "1234"},
        )

    def test_giftcards_pay_sends_cardnumber_and_pin_on_the_wire(
        self, recording_buckaroo, recording_mock
    ):
        """service_parameters dict must reach ServiceList[0].Parameters.

        Top-level param names keep their internal casing, so ``"PIN"`` reaches
        the wire as ``"PIN"``. Assert both the value pairing and the presence
        of both keys so a builder that silently drops service_parameters would
        fail.
        """
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                Helpers.pending_redirect_response("giftcards"),
            )
        )
        recording_buckaroo.payments.create_payment(
            "giftcards",
            Helpers.standard_payload(
                invoice="INV-GC-WIRE",
                giftcard_name="other",
                service_parameters={"Cardnumber": "1234567890123456", "PIN": "1234"},
            ),
        ).pay()

        assert recorded_action(recording_mock) == "Pay"
        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(recording_mock)}
        assert params.get("Cardnumber") == "1234567890123456"
        assert params.get("PIN") == "1234"

    def test_giftcards_pay_redirect_mode_omits_card_parameters(
        self, recording_buckaroo, recording_mock
    ):
        """Redirect mode: no giftcard_name and no card details — payload reaches
        the gateway with no Cardnumber/PIN and an empty service-parameter list.
        Buckaroo's hosted page collects card details there.
        """
        recording_mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/transaction*",
                Helpers.pending_redirect_response("giftcards"),
            )
        )
        recording_buckaroo.payments.create_payment(
            "giftcards",
            Helpers.standard_payload(
                invoice="INV-GC-REDIRECT",
                services_selectable_by_client="fashioncheque,intersolve,tcs",
            ),
        ).pay()

        assert recorded_action(recording_mock) == "Pay"
        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(recording_mock)}
        assert params == {}
