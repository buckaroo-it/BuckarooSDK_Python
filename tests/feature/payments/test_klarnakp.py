"""Feature test: klarnakp pay() and reserve() round-trips through full stack with MockBuckaroo."""

from tests.support.mock_request import BuckarooMockRequest
from tests.support.test_helpers import TestHelpers


class TestKlarnakpFeature:
    def test_klarnakp_pay_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response(
            "klarnakp", overrides={"AmountDebit": 25.00}
        )
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", response_body)
        )
        response = buckaroo.payments.create_payment("klarnakp", TestHelpers.standard_payload(
            invoice="INV-KKP-001",
            amount=25.00,
            description="Test klarnakp",
            service_parameters={
                "reservationNumber": "RES-12345",
            },
        )).pay()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        assert response.currency == "EUR"
        assert response.amount_debit == 25.00

    def test_klarnakp_reserve_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response(
            "klarnakp", overrides={"AmountDebit": 50.00}
        )
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body)
        )
        response = buckaroo.payments.create_payment("klarnakp", TestHelpers.standard_payload(
            invoice="INV-KKP-002",
            amount=50.00,
            description="Test klarnakp reserve",
            service_parameters={
                "operatingCountry": "NL",
                "article": [
                    {"description": "Widget", "quantity": "2", "price": "25.00"},
                ],
            },
        )).reserve()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        assert response.currency == "EUR"
        assert response.amount_debit == 50.00

    def test_klarnakp_cancel_reservation_returns_pending(self, buckaroo, mock_strategy):
        response_body = TestHelpers.pending_redirect_response(
            "klarnakp", overrides={"AmountDebit": 25.00}
        )
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body)
        )
        response = buckaroo.payments.create_payment("klarnakp", TestHelpers.standard_payload(
            invoice="INV-KKP-003",
            amount=25.00,
            description="Test klarnakp cancel reservation",
            service_parameters={
                "reservationNumber": "RES-12345",
            },
        )).cancelReservation()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
