"""Unit tests for :class:`EmandateBuilder`."""

from __future__ import annotations

import pytest

from buckaroo.builders.solutions.emandate_builder import EmandateB2BBuilder, EmandateBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action


def test_construction_with_client_succeeds(client):
    builder = EmandateBuilder(client)
    assert isinstance(builder, EmandateBuilder)
    assert isinstance(builder, SolutionBuilder)


def test_get_service_name_returns_emandate(client):
    assert EmandateBuilder(client).get_service_name() == "emandate"


def test_get_allowed_service_parameters_get_issuer_list_returns_empty(client):
    builder = EmandateBuilder(client)
    assert builder.get_allowed_service_parameters("GetIssuerList") == {}


def test_get_allowed_service_parameters_is_case_insensitive(client):
    builder = EmandateBuilder(client)
    assert builder.get_allowed_service_parameters("getissuerlist") == (
        builder.get_allowed_service_parameters("GetIssuerList")
    )


def test_get_allowed_service_parameters_create_mandate_marks_debtor_reference_required(client):
    builder = EmandateBuilder(client)
    params = builder.get_allowed_service_parameters("CreateMandate")

    assert set(params.keys()) == {
        "debtorBankId",
        "debtorReference",
        "sequenceType",
        "purchaseId",
        "language",
        "emandateReason",
        "maxAmount",
    }
    assert params["debtorReference"]["required"] is True
    for name, config in params.items():
        if name != "debtorReference":
            assert config["required"] is False, f"{name} should be optional"


def test_get_allowed_service_parameters_create_mandate_is_case_insensitive(client):
    builder = EmandateBuilder(client)
    assert builder.get_allowed_service_parameters("createmandate") == (
        builder.get_allowed_service_parameters("CreateMandate")
    )


def test_issuer_list_posts_to_data_request_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "emandate-key-123",
                "Status": {"Code": {"Code": 190}},
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
            },
        )
    )

    response = EmandateBuilder(client).issuer_list()

    assert response.key == "emandate-key-123"
    assert response.get_service_parameter("Issuer") == "ABNANL2A"
    assert response.get_service_parameter("IssuerName") == "ABN AMRO"
    assert recorded_action(mock_strategy) == "GetIssuerList"


def test_create_mandate_posts_to_data_request_and_parses_mandate_id(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "emandate-key-456",
                "Status": {"Code": {"Code": 190}},
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "CreateMandate",
                        "Parameters": [
                            {"Name": "MandateId", "Value": "MND-001"},
                        ],
                    }
                ],
            },
        )
    )

    builder = EmandateBuilder(client)
    builder.add_parameter("debtorReference", "DEBTOR-001")
    response = builder.create_mandate()

    assert response.key == "emandate-key-456"
    assert response.get_service_parameter("MandateId") == "MND-001"
    assert recorded_action(mock_strategy) == "CreateMandate"


def test_create_mandate_raises_when_debtor_reference_missing(client):
    builder = EmandateBuilder(client)

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.create_mandate()

    assert exc.value.parameter_name == "debtorReference"


def test_get_allowed_service_parameters_get_status_marks_mandate_id_required(client):
    builder = EmandateBuilder(client)
    params = builder.get_allowed_service_parameters("GetStatus")

    assert set(params.keys()) == {"mandateId"}
    assert params["mandateId"]["required"] is True


def test_get_allowed_service_parameters_get_status_is_case_insensitive(client):
    builder = EmandateBuilder(client)
    assert builder.get_allowed_service_parameters("getstatus") == (
        builder.get_allowed_service_parameters("GetStatus")
    )


def test_status_posts_to_data_request_and_parses_status(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "emandate-key-789",
                "Status": {"Code": {"Code": 190}},
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "GetStatus",
                        "Parameters": [
                            {"Name": "Status", "Value": "Active"},
                        ],
                    }
                ],
            },
        )
    )

    builder = EmandateBuilder(client)
    builder.add_parameter("mandateId", "MND-001")
    response = builder.status()

    assert response.key == "emandate-key-789"
    assert response.get_service_parameter("Status") == "Active"
    assert recorded_action(mock_strategy) == "GetStatus"


def test_status_raises_when_mandate_id_missing(client):
    builder = EmandateBuilder(client)

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.status()

    assert exc.value.parameter_name == "mandateId"


def test_get_allowed_service_parameters_modify_mandate_marks_mandate_id_required(client):
    builder = EmandateBuilder(client)
    params = builder.get_allowed_service_parameters("ModifyMandate")

    assert set(params.keys()) == {"mandateId", "maxAmount", "language", "emandateReason"}
    assert params["mandateId"]["required"] is True
    for name, config in params.items():
        if name != "mandateId":
            assert config["required"] is False, f"{name} should be optional"


def test_get_allowed_service_parameters_modify_mandate_is_case_insensitive(client):
    builder = EmandateBuilder(client)
    assert builder.get_allowed_service_parameters("modifymandate") == (
        builder.get_allowed_service_parameters("ModifyMandate")
    )


def test_modify_mandate_posts_to_data_request_and_parses_mandate_id(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "emandate-key-321",
                "Status": {"Code": {"Code": 190}},
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "ModifyMandate",
                        "Parameters": [
                            {"Name": "MandateId", "Value": "MND-002"},
                        ],
                    }
                ],
            },
        )
    )

    builder = EmandateBuilder(client)
    builder.add_parameter("mandateId", "MND-002")
    builder.add_parameter("maxAmount", "500.00")
    response = builder.modify_mandate()

    assert response.key == "emandate-key-321"
    assert response.get_service_parameter("MandateId") == "MND-002"
    assert recorded_action(mock_strategy) == "ModifyMandate"


def test_modify_mandate_raises_when_mandate_id_missing(client):
    builder = EmandateBuilder(client)

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.modify_mandate()

    assert exc.value.parameter_name == "mandateId"


def test_get_allowed_service_parameters_cancel_mandate_marks_mandate_id_required(client):
    builder = EmandateBuilder(client)
    params = builder.get_allowed_service_parameters("CancelMandate")

    assert set(params.keys()) == {"mandateId", "purchaseId"}
    assert params["mandateId"]["required"] is True
    assert params["purchaseId"]["required"] is False


def test_get_allowed_service_parameters_cancel_mandate_is_case_insensitive(client):
    builder = EmandateBuilder(client)
    assert builder.get_allowed_service_parameters("cancelmandate") == (
        builder.get_allowed_service_parameters("CancelMandate")
    )


def test_cancel_mandate_posts_to_data_request_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {
                "Key": "emandate-key-654",
                "Status": {"Code": {"Code": 190}},
                "Services": [
                    {
                        "Name": "emandate",
                        "Action": "CancelMandate",
                        "Parameters": [],
                    }
                ],
            },
        )
    )

    builder = EmandateBuilder(client)
    builder.add_parameter("mandateId", "MND-003")
    response = builder.cancel_mandate()

    assert response.key == "emandate-key-654"
    assert recorded_action(mock_strategy) == "CancelMandate"


def test_cancel_mandate_raises_when_mandate_id_missing(client):
    builder = EmandateBuilder(client)

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.cancel_mandate()

    assert exc.value.parameter_name == "mandateId"


def test_b2b_get_service_name_returns_emandateb2b(client):
    assert EmandateB2BBuilder(client).get_service_name() == "emandateb2b"


def test_b2b_builder_is_a_subclass_of_emandate_builder(client):
    builder = EmandateB2BBuilder(client)
    assert isinstance(builder, EmandateBuilder)
