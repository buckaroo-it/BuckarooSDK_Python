import pytest

from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers
from tests.support.recording_mock import recorded_action, recorded_request


def _ideal_payload(**overrides):
    """Base iDEAL transaction fields used to fund a split."""
    payload = {
        "currency": "EUR",
        "amount": 95.00,
        "description": "Split order INV0001",
        "invoice": "INV0001",
        "return_url": "https://example.com/return",
        "return_url_cancel": "https://example.com/cancel",
        "return_url_error": "https://example.com/error",
        "return_url_reject": "https://example.com/reject",
        "service_parameters": {"issuer": "ABNANL2A"},
    }
    payload.update(overrides)
    return payload


def _split_response():
    """Buckaroo-shaped Split response carrying the SplitGuid identifiers."""
    return Helpers.success_response(
        {
            "Services": [
                {
                    "Name": "Marketplaces",
                    "Action": None,
                    "Parameters": [
                        {"Name": "SplitGuid_Marketplace", "Value": "GUID-MARKETPLACE"},
                        {"Name": "SplitGuid_Seller_1", "Value": "GUID-SELLER-1"},
                    ],
                },
                {"Name": "ideal", "Action": None, "Parameters": []},
            ],
            "ServiceCode": "ideal",
        }
    )


class TestMarketplacesSplit:
    """Split rides on an iDEAL payment via combine()."""

    def test_marketplaces_is_available(self, buckaroo):
        assert buckaroo.solutions.is_method_supported("marketplaces")

    def test_service_name_is_marketplaces(self, buckaroo):
        assert (
            buckaroo.solutions.create_solution("marketplaces").get_service_name() == "Marketplaces"
        )

    def test_split_combines_marketplaces_into_ideal_pay(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", _split_response())
        )

        mp = buckaroo.solutions.create_solution("marketplaces").split(
            {
                "daysUntilTransfer": "2",
                "marketplace": {"Amount": "10.00", "Description": "INV0001 Commission Platform"},
                "sellers": [
                    {"AccountId": "789C60F316D24B088ACD471", "Amount": "50.00"},
                    {"AccountId": "369C60F316D24B088ACD238", "Amount": "35.00"},
                ],
            }
        )
        response = buckaroo.payments.create_payment("ideal", _ideal_payload()).combine(mp).pay()

        body = recorded_request(mock_strategy)
        services = body["Services"]["ServiceList"]
        # Payment method first, combined Marketplaces service second.
        assert [s["Name"] for s in services] == ["ideal", "Marketplaces"]
        assert services[0]["Action"] == "Pay"
        assert services[1]["Action"] == "Split"
        assert body["Currency"] == "EUR"
        assert body["AmountDebit"] == 95.00

        ideal_params = {p["Name"]: p["Value"] for p in services[0]["Parameters"]}
        assert ideal_params["Issuer"] == "ABNANL2A"

        split = {
            (p["Name"], p["GroupType"], p["GroupID"]): p["Value"] for p in services[1]["Parameters"]
        }
        assert split[("DaysUntilTransfer", "", "")] == "2"
        assert split[("Amount", "Marketplace", "")] == "10.00"
        assert split[("Accountid", "Seller", "1")] == "789C60F316D24B088ACD471"
        assert split[("Accountid", "Seller", "2")] == "369C60F316D24B088ACD238"

        assert response.get_service_parameter("SplitGuid_Marketplace") == "GUID-MARKETPLACE"
        assert response.get_service_parameter("SplitGuid_Seller_1") == "GUID-SELLER-1"


def _datarequest_response(action):
    return Helpers.success_response({"Services": None, "ServiceCode": "Marketplaces"})


class TestMarketplacesTransfer:
    """Standalone Transfer posts a DataRequest."""

    def test_transfer_all_posts_datarequest(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", "*/json/DataRequest", _datarequest_response("Transfer")
            )
        )

        response = buckaroo.solutions.create_solution("marketplaces").transfer(
            {"originalTransactionKey": "D3732474ED0"}
        )

        body = recorded_request(mock_strategy)
        services = body["Services"]["ServiceList"]
        assert body["OriginalTransactionKey"] == "D3732474ED0"
        assert "AmountDebit" not in body
        assert len(services) == 1
        assert services[0]["Name"] == "Marketplaces"
        assert recorded_action(mock_strategy) == "Transfer"
        assert "Parameters" not in services[0]
        assert response.status.code.code == 190

    def test_transfer_with_splits_posts_grouped_params(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", "*/json/DataRequest", _datarequest_response("Transfer")
            )
        )

        buckaroo.solutions.create_solution("marketplaces").transfer(
            {
                "originalTransactionKey": "D3732474ED0",
                "marketplace": {"Amount": "10.00", "Description": "Commission"},
                "sellers": [{"AccountId": "789C60F316D24B088ACD471", "Amount": "50.00"}],
            }
        )

        service = recorded_request(mock_strategy)["Services"]["ServiceList"][0]
        assert service["Action"] == "Transfer"
        params = {
            (p["Name"], p["GroupType"], p["GroupID"]): p["Value"] for p in service["Parameters"]
        }
        assert params[("Amount", "Marketplace", "")] == "10.00"
        assert params[("Accountid", "Seller", "1")] == "789C60F316D24B088ACD471"
        # DaysUntilTransfer never applies to a Transfer.
        assert not any(name == "DaysUntilTransfer" for name, _, _ in params)

    def test_transfer_requires_original_key(self, buckaroo):
        with pytest.raises(ValueError):
            buckaroo.solutions.create_solution("marketplaces").transfer({})


def _refund_supplementary_response():
    return Helpers.success_response(
        {
            "Services": [{"Name": "ideal", "Action": None, "Parameters": []}],
            "ServiceCode": "ideal",
            "AmountCredit": 50.00,
            "AmountDebit": None,
        }
    )


class TestMarketplacesRefundSupplementary:
    """RefundSupplementary rides on an iDEAL refund via combine()."""

    def test_refund_supplementary_all_combines_into_refund(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", _refund_supplementary_response())
        )

        mp = buckaroo.solutions.create_solution("marketplaces").refund_supplementary()
        payload = Helpers.standard_payload(
            invoice="INV0001",
            original_transaction_key="D3737EDA42474ED0",
            refund_amount=50.00,
        )
        response = buckaroo.payments.create_payment("ideal", payload).combine(mp).refund()

        body = recorded_request(mock_strategy)
        services = body["Services"]["ServiceList"]
        assert [(s["Name"], s["Action"]) for s in services] == [
            ("ideal", "Refund"),
            ("Marketplaces", "RefundSupplementary"),
        ]
        assert body["OriginalTransactionKey"] == "D3737EDA42474ED0"
        assert body["AmountCredit"] == 50.00
        assert "Parameters" not in services[1]
        assert response.status.code.code == 190

    def test_refund_supplementary_with_sellers(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json("POST", "*/json/transaction", _refund_supplementary_response())
        )

        mp = buckaroo.solutions.create_solution("marketplaces").refund_supplementary(
            {"sellers": [{"AccountId": "789C60F316D24B088ACD471", "Amount": "30.00"}]}
        )
        payload = Helpers.standard_payload(
            invoice="INV0001",
            original_transaction_key="D3737EDA42474ED0",
            refund_amount=30.00,
        )
        buckaroo.payments.create_payment("ideal", payload).combine(mp).refund()

        service = recorded_request(mock_strategy)["Services"]["ServiceList"][1]
        assert service["Action"] == "RefundSupplementary"
        params = {
            (p["Name"], p["GroupType"], p["GroupID"]): p["Value"] for p in service["Parameters"]
        }
        assert params[("Accountid", "Seller", "1")] == "789C60F316D24B088ACD471"
        assert params[("Amount", "Seller", "1")] == "30.00"


class TestMarketplacesManualTransfer:
    """Standalone ManualTransfer posts a DataRequest."""

    def test_manual_transfer_posts_accounts_and_amount(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", "*/json/DataRequest", _datarequest_response("ManualTransfer")
            )
        )

        response = buckaroo.solutions.create_solution("marketplaces").manual_transfer(
            {
                "fromAccountId": "AAAAAAAAAAAAAAAAAAA",
                "toAccountId": "BBBBBBBBBBBBBBBBBBB",
                "fromDescription": "Deduction monthly fee",
                "toDescription": "Monthly fee third party ABC",
                "amount": 10.00,
                "currency": "EUR",
                "invoice": "INV0001",
            }
        )

        body = recorded_request(mock_strategy)
        service = body["Services"]["ServiceList"][0]
        assert service["Name"] == "Marketplaces"
        assert service["Action"] == "ManualTransfer"
        assert body["Currency"] == "EUR"
        assert body["Amount"] == 10.00
        assert "AmountDebit" not in body

        params = {p["Name"]: p["Value"] for p in service["Parameters"]}
        assert params["FromAccountId"] == "AAAAAAAAAAAAAAAAAAA"
        assert params["ToAccountId"] == "BBBBBBBBBBBBBBBBBBB"
        assert params["FromDescription"] == "Deduction monthly fee"
        assert params["ToDescription"] == "Monthly fee third party ABC"
        assert response.status.code.code == 190

    def test_manual_transfer_requires_all_fields(self, buckaroo):
        with pytest.raises(ValueError):
            buckaroo.solutions.create_solution("marketplaces").manual_transfer(
                {
                    "fromAccountId": "AAA",
                    "toAccountId": "",
                    "fromDescription": "fee",
                    "toDescription": "fee",
                    "amount": 10.00,
                }
            )

    def test_manual_transfer_omits_invoice_when_absent(self, buckaroo, mock_strategy):
        mock_strategy.queue(
            BuckarooMockRequest.json(
                "POST", "*/json/DataRequest", _datarequest_response("ManualTransfer")
            )
        )

        buckaroo.solutions.create_solution("marketplaces").manual_transfer(
            {
                "fromAccountId": "AAA",
                "toAccountId": "BBB",
                "fromDescription": "fee",
                "toDescription": "fee",
                "amount": 10.00,
                "currency": "EUR",
            }
        )

        assert "Invoice" not in recorded_request(mock_strategy)

    def test_manual_transfer_requires_amount(self, buckaroo):
        with pytest.raises(ValueError, match="amount"):
            buckaroo.solutions.create_solution("marketplaces").manual_transfer(
                {
                    "fromAccountId": "AAA",
                    "toAccountId": "BBB",
                    "fromDescription": "fee",
                    "toDescription": "fee",
                    "currency": "EUR",
                }
            )

    def test_manual_transfer_requires_currency(self, buckaroo):
        with pytest.raises(ValueError, match="currency"):
            buckaroo.solutions.create_solution("marketplaces").manual_transfer(
                {
                    "fromAccountId": "AAA",
                    "toAccountId": "BBB",
                    "fromDescription": "fee",
                    "toDescription": "fee",
                    "amount": 10.00,
                }
            )
