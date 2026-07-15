import json

from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers


class TestBankingFeature:
    """Feature tests for Banking payouts (PaymentOrder action).

    Banking is a payout with no return URLs, so the payload is built
    directly here rather than via ``Helpers.standard_payload`` (which
    injects return_url* fields that don't apply to a server-to-server
    payout).
    """

    def test_banking_payment_order_returns_success(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [{"Name": "Banking", "Action": "PaymentOrder", "Parameters": []}],
                "ServiceCode": "banking",
                "AmountCredit": 150.0,
                "AmountDebit": None,
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/transaction", response_body))

        response = buckaroo.payments.create_payment(
            "banking",
            {
                "currency": "EUR",
                "amount": 150.0,
                "invoice": "Banking_Test_1",
                "description": "Test",
                "service_parameters": {
                    "AccountHolderName": "Arensman",
                    "IBAN": "NL44RABO0123456789",
                },
            },
        ).payment_order()

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]

        sent = json.loads(mock_strategy.calls[-1]["data"])
        assert sent["Currency"] == "EUR"
        assert sent["AmountCredit"] == 150.0
        assert "AmountDebit" not in sent
        assert sent["Invoice"] == "Banking_Test_1"
        assert sent["Description"] == "Test"

        service = sent["Services"]["ServiceList"][0]
        assert service["Name"] == "Banking"
        assert service["Action"] == "PaymentOrder"
        assert {"Name": "Accountholdername", "Value": "Arensman"} in [
            {"Name": p["Name"], "Value": p["Value"]} for p in service["Parameters"]
        ]
        assert {"Name": "Iban", "Value": "NL44RABO0123456789"} in [
            {"Name": p["Name"], "Value": p["Value"]} for p in service["Parameters"]
        ]
