import pytest

from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError
from tests.support.mock_request import BuckarooMockRequest
from tests.support.helpers import Helpers
from tests.support.recording_mock import (
    recorded_action,
    recorded_request,
    recorded_service_parameters,
)


class TestEmandateFeature:
    """Feature tests for the eMandate solution."""

    def test_issuer_list_returns_issuers(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "GetIssuerList",
                        "Parameters": [
                            {"Name": "Issuer", "Value": "ABNANL2A"},
                            {"Name": "IssuerName", "Value": "ABN AMRO"},
                        ],
                    }
                ],
                "ServiceCode": "emandate",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution("emandate").issuer_list()

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
        assert response.get_service_parameter("Issuer") == "ABNANL2A"
        assert response.get_service_parameter("IssuerName") == "ABN AMRO"
        assert recorded_action(mock_strategy) == "GetIssuerList"

    def test_emandate_is_available(self, buckaroo):
        assert buckaroo.solutions.is_method_supported("emandate")

    def test_create_mandate_posts_service_parameters_and_returns_mandate_id(
        self, buckaroo, mock_strategy
    ):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "CreateMandate",
                        "Parameters": [{"Name": "MandateId", "Value": "MND-999"}],
                    }
                ],
                "ServiceCode": "emandate",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "emandate",
            {
                "service_parameters": {
                    "debtorReference": "DEBTOR-999",
                    "sequenceType": "1",
                    "purchaseId": "PUR-1",
                }
            },
        ).create_mandate()

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
        assert response.get_service_parameter("MandateId") == "MND-999"
        assert recorded_action(mock_strategy) == "CreateMandate"

        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert params["DebtorReference"] == "DEBTOR-999"
        assert params["SequenceType"] == "1"
        assert params["PurchaseId"] == "PUR-1"

    def test_create_mandate_without_debtor_reference_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution("emandate")

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.create_mandate()

        assert exc.value.parameter_name == "debtorReference"

    def test_status_posts_mandate_id_and_returns_status(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "GetStatus",
                        "Parameters": [{"Name": "Status", "Value": "Active"}],
                    }
                ],
                "ServiceCode": "emandate",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "emandate",
            {"service_parameters": {"mandateId": "MND-777"}},
        ).status()

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
        assert response.get_service_parameter("Status") == "Active"
        assert recorded_action(mock_strategy) == "GetStatus"

        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert params["MandateId"] == "MND-777"

    def test_status_without_mandate_id_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution("emandate")

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.status()

        assert exc.value.parameter_name == "mandateId"

    def test_modify_mandate_posts_service_parameters_and_returns_mandate_id(
        self, buckaroo, mock_strategy
    ):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "ModifyMandate",
                        "Parameters": [{"Name": "MandateId", "Value": "MND-555"}],
                    }
                ],
                "ServiceCode": "emandate",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "emandate",
            {
                "service_parameters": {
                    "mandateId": "MND-555",
                    "maxAmount": "1000.00",
                }
            },
        ).modify_mandate()

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
        assert response.get_service_parameter("MandateId") == "MND-555"
        assert recorded_action(mock_strategy) == "ModifyMandate"

        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert params["MandateId"] == "MND-555"
        assert params["MaxAmount"] == "1000.00"

    def test_modify_mandate_without_mandate_id_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution("emandate")

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.modify_mandate()

        assert exc.value.parameter_name == "mandateId"

    def test_cancel_mandate_posts_service_parameters_and_returns_response(
        self, buckaroo, mock_strategy
    ):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "CancelMandate",
                        "Parameters": [],
                    }
                ],
                "ServiceCode": "emandate",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "emandate",
            {
                "service_parameters": {
                    "mandateId": "MND-321",
                    "purchaseId": "PUR-2",
                }
            },
        ).cancel_mandate()

        assert response.status.code.code == 190
        assert response.key == response_body["Key"]
        assert recorded_action(mock_strategy) == "CancelMandate"

        params = {p["Name"]: p["Value"] for p in recorded_service_parameters(mock_strategy)}
        assert params["MandateId"] == "MND-321"
        assert params["PurchaseId"] == "PUR-2"

    def test_cancel_mandate_without_mandate_id_raises_before_wire(self, buckaroo):
        builder = buckaroo.solutions.create_solution("emandate")

        with pytest.raises(RequiredParameterMissingError) as exc:
            builder.cancel_mandate()

        assert exc.value.parameter_name == "mandateId"


class TestEmandateB2BFeature:
    """Feature tests for the Business (B2B) eMandate variant."""

    def test_b2b_is_available(self, buckaroo):
        assert buckaroo.solutions.is_method_supported("emandateb2b")

    def test_create_mandate_posts_under_emandateb2b_service_name(self, buckaroo, mock_strategy):
        response_body = Helpers.success_response(
            {
                "Services": [
                    {
                        "Name": "emandateb2b",
                        "Action": "CreateMandate",
                        "Parameters": [{"Name": "MandateId", "Value": "MND-B2B-1"}],
                    }
                ],
                "ServiceCode": "emandateb2b",
            }
        )
        mock_strategy.queue(BuckarooMockRequest.json("POST", "*/json/DataRequest", response_body))

        response = buckaroo.solutions.create_solution(
            "emandateb2b",
            {"service_parameters": {"debtorReference": "DEBTOR-B2B-1"}},
        ).create_mandate()

        assert response.status.code.code == 190
        assert response.get_service_parameter("MandateId") == "MND-B2B-1"
        assert recorded_action(mock_strategy) == "CreateMandate"

        service = recorded_request(mock_strategy)["Services"]["ServiceList"][0]
        assert service["Name"].lower() == "emandateb2b"
