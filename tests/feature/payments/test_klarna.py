"""Feature test: klarna reserve() + pay-as-capture round-trips through full stack with MockBuckaroo."""

import json

from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestKlarnaFeature:
    def test_klarna_reserve_returns_pending_with_redirect(self, buckaroo, mock_strategy):
        response_body = Helpers.pending_redirect_response(
            "klarna", action="Reserve", overrides={"AmountDebit": 50.00}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))
        response = buckaroo.payments.create_payment(
            "klarna",
            Helpers.standard_payload(
                invoice="INV-KLARNA-002",
                amount=50.00,
                description="Test klarna reserve",
                service_parameters={
                    "article": [
                        {"description": "Widget", "quantity": "2", "price": "25.00"},
                    ],
                    "billingCustomer": [{"firstName": "John", "lastName": "Doe"}],
                    "shippingCustomer": [{"firstName": "John", "lastName": "Doe"}],
                    "operatingCountry": "NL",
                },
            ),
        ).reserve()

        assert response.is_pending()
        assert response.get_redirect_url() is not None
        assert response.key == response_body["Key"]
        assert response.currency == "EUR"
        assert response.amount_debit == 50.00

    def test_klarna_pay_as_capture_attaches_data_request_key(self, buckaroo, mock_strategy):
        """Pay-as-capture references the prior Reserve via the ``dataRequestKey``
        service parameter (callers add it before calling ``.pay()``)."""
        capture_body = Helpers.success_response(
            overrides={"Key": "PAY-K-1", "AmountDebit": 25.00, "ServiceCode": "klarna"}
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", capture_body))

        builder = buckaroo.payments.create_payment(
            "klarna",
            Helpers.standard_payload(
                invoice="INV-KLARNA-CAP-A",
                amount=25.00,
                description="Test klarna capture",
            ),
        )
        builder.add_parameter("dataRequestKey", "RES-DRK-1")
        response = builder.pay()

        assert response.key == "PAY-K-1"
        body = json.loads(mock_strategy.calls[-1]["data"])
        services = body["Services"]["ServiceList"]
        names = [p["Name"] for p in services[0]["Parameters"]]
        assert "Datarequestkey" in names
