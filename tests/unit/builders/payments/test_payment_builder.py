"""Tests for :class:`buckaroo.builders.payments.payment_builder.PaymentBuilder`.

Exercises :class:`PaymentBuilder` via the shared ``make_test_builder`` helper.
Assertions read off the public API — ``PaymentRequest.to_dict()`` and recorded
HTTP calls — never builder internals.
"""

from __future__ import annotations

import json

import pytest

from buckaroo.exceptions._parameter_validation_error import (
    RequiredParameterMissingError,
)
from buckaroo.http.client import BuckarooApiError
from tests.support.builders import (
    make_test_builder,
    populate_required_fields,
    strip_amount_debit_from_build,
)
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


# ---------------------------------------------------------------------------
# build(action="Pay") — basic shape


def test_build_pay_sets_service_name_and_action():
    builder = populate_required_fields(make_test_builder(object(), service_name="ideal"), amount=10.50)

    request = builder.build("Pay", validate=False).to_dict()

    service = request["Services"]["ServiceList"][0]
    assert service["Name"] == "ideal"
    assert service["Action"] == "Pay"


# ---------------------------------------------------------------------------
# build() — required service parameter validation


def test_build_pay_raises_when_required_service_parameter_missing():
    allowed = {
        "Pay": {
            "issuer": {"type": str, "required": True},
        }
    }
    builder = populate_required_fields(
        make_test_builder(object(), service_name="ideal", allowed_params=allowed),
        amount=10.50,
    )

    with pytest.raises(RequiredParameterMissingError) as exc:
        builder.build("Pay", strict_validation=True)

    assert "issuer" in str(exc.value)
    assert exc.value.parameter_name == "issuer"


def test_build_pay_with_validate_false_skips_required_parameter_check():
    allowed = {
        "Pay": {
            "issuer": {"type": str, "required": True},
        }
    }
    builder = populate_required_fields(
        make_test_builder(object(), service_name="ideal", allowed_params=allowed),
        amount=10.50,
    )

    request = builder.build("Pay", validate=False).to_dict()

    service = request["Services"]["ServiceList"][0]
    assert service["Name"] == "ideal"
    assert service["Action"] == "Pay"


def test_build_pay_filters_parameters_not_in_allowed_service_parameters():
    allowed = {
        "Pay": {
            "issuer": {"type": str, "required": False},
        }
    }
    builder = populate_required_fields(
        make_test_builder(object(), service_name="ideal", allowed_params=allowed),
        amount=10.50,
    )
    builder.add_parameter("issuer", "INGBNL2A")
    builder.add_parameter("rogue", "should-vanish")

    request = builder.build("Pay").to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]

    names = [p["Name"] for p in params]
    assert "Issuer" in names
    assert "Rogue" not in names


# ---------------------------------------------------------------------------
# pay() — builds Pay request, posts to /json/transaction, returns PaymentResponse


def test_pay_posts_build_pay_request_to_transaction_endpoint():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "PAY-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(make_test_builder(client, service_name="ideal"), amount=10.50)
    response = builder.pay(validate=False)

    assert mock.calls[0]["method"] == "POST"
    assert "/json/transaction" in mock.calls[0]["url"].lower()

    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "ideal"
    assert service["Action"] == "Pay"

    assert response.key == "PAY-1"
    mock.assert_all_consumed()


def test_post_transaction_uses_injected_client_and_returns_parsed_payment_response():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "T-99", "Invoice": "INV-1"},
        )
    )

    builder = populate_required_fields(make_test_builder(client, service_name="ideal"), amount=10.50)
    request = builder.build("Pay", validate=False)

    response = builder._post_transaction(request.to_dict())

    assert response.key == "T-99"
    assert response.invoice == "INV-1"
    mock.assert_all_consumed()


# ---------------------------------------------------------------------------
# Error propagation


def test_post_transaction_propagates_buckaroo_error_from_http_client():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST", "*/json/transaction*", {"error": "boom"}, status=500
        )
    )

    builder = populate_required_fields(make_test_builder(client, service_name="ideal"), amount=10.50)

    with pytest.raises(BuckarooApiError):
        builder.pay(validate=False)

    mock.assert_all_consumed()


# ---------------------------------------------------------------------------
# Fluent setters (PaymentBuilder re-declares these over BaseBuilder)


FLUENT_SETTERS = [
    ("currency", "EUR", "Currency"),
    ("amount", 12.34, "AmountDebit"),
    ("description", "payment description", "Description"),
    ("invoice", "INV-42", "Invoice"),
    ("return_url", "https://example.com/ok", "ReturnURL"),
    ("return_url_cancel", "https://example.com/cancel", "ReturnURLCancel"),
    ("return_url_error", "https://example.com/error", "ReturnURLError"),
    ("return_url_reject", "https://example.com/reject", "ReturnURLReject"),
]


@pytest.mark.parametrize("setter,value,dict_key", FLUENT_SETTERS)
def test_fluent_setter_returns_self_and_appears_in_request(setter, value, dict_key):
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    result = getattr(builder, setter)(value)
    assert result is builder

    request = builder.build(validate=False).to_dict()
    assert request[dict_key] == value


def test_continue_on_incomplete_setter_returns_self_and_appears_in_request():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    assert builder.continue_on_incomplete("0") is builder
    request = builder.build(validate=False).to_dict()
    assert request["ContinueOnIncomplete"] == "0"


def test_client_ip_setter_returns_self_and_appears_in_request():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    assert builder.client_ip("203.0.113.7", ip_type=1) is builder
    request = builder.build(validate=False).to_dict()
    assert request["ClientIP"] == {"Type": 1, "Address": "203.0.113.7"}


# ---------------------------------------------------------------------------
# add_parameter


def test_add_parameter_flat_returns_self_and_capitalizes_name():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    result = builder.add_parameter("issuer", "INGBNL2A")
    assert result is builder

    request = builder.build(validate=False).to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]
    assert params == [
        {"Name": "Issuer", "GroupType": "", "GroupID": "", "Value": "INGBNL2A"}
    ]


def test_add_parameter_grouped_sets_group_type_and_group_id():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.add_parameter("firstName", "Jane", group_type="customer", group_id="7")

    request = builder.build(validate=False).to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]
    assert params == [
        {"Name": "Firstname", "GroupType": "Customer", "GroupID": "7", "Value": "Jane"}
    ]


def test_add_parameter_boolean_values_are_lowercased_strings():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.add_parameter("enabled", True)
    builder.add_parameter("disabled", False)

    request = builder.build(validate=False).to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]
    assert params[0]["Value"] == "true"
    assert params[1]["Value"] == "false"


def test_add_parameter_with_list_of_dicts_adds_grouped_batch():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.add_parameter(
        "articles",
        [
            {"name": "Item A", "quantity": 2},
            {"name": "Item B", "quantity": 1},
        ],
    )

    request = builder.build(validate=False).to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]
    assert params == [
        {"Name": "Name", "GroupType": "Articles", "GroupID": "1", "Value": "Item A"},
        {"Name": "Quantity", "GroupType": "Articles", "GroupID": "1", "Value": "2"},
        {"Name": "Name", "GroupType": "Articles", "GroupID": "2", "Value": "Item B"},
        {"Name": "Quantity", "GroupType": "Articles", "GroupID": "2", "Value": "1"},
    ]


def test_add_parameter_with_list_of_non_dicts_is_ignored():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.add_parameter("articles", ["not-a-dict", 42])

    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert "Parameters" not in service


# ---------------------------------------------------------------------------
# Validator convenience passthroughs


def test_is_parameter_allowed_delegates_to_validator():
    allowed = {"Pay": {"issuer": {"type": str, "required": False}}}
    builder = make_test_builder(object(), allowed_params=allowed)
    assert builder.is_parameter_allowed("issuer", "Pay") is True
    assert builder.is_parameter_allowed("nope", "Pay") is False


def test_get_parameter_info_returns_allowed_params_for_action():
    allowed = {"Pay": {"issuer": {"type": str, "required": False}}}
    builder = make_test_builder(object(), allowed_params=allowed)
    assert builder.get_parameter_info("Pay") == allowed["Pay"]


def test_get_normalized_parameter_name_returns_canonical_name():
    allowed = {"Pay": {"issuer": {"type": str, "required": False}}}
    builder = make_test_builder(object(), allowed_params=allowed)
    assert builder.get_normalized_parameter_name("Issuer", "Pay") == "issuer"
    assert builder.get_normalized_parameter_name("unknown", "Pay") == ""


# ---------------------------------------------------------------------------
# from_dict


def test_from_dict_populates_all_supported_core_fields_and_returns_self():
    builder = make_test_builder(object())
    data = {
        "currency": "EUR",
        "amount": 99.99,
        "description": "hello",
        "invoice": "INV-9",
        "return_url": "https://example.com/ok",
        "return_url_cancel": "https://example.com/cancel",
        "return_url_error": "https://example.com/error",
        "return_url_reject": "https://example.com/reject",
        "continue_on_incomplete": "0",
        "push_url": "https://example.com/push",
        "push_url_failure": "https://example.com/push-fail",
        "client_ip": "198.51.100.9",
    }

    result = builder.from_dict(data)
    assert result is builder

    request = builder.build(validate=False).to_dict()
    assert request["Currency"] == "EUR"
    assert request["AmountDebit"] == 99.99
    assert request["Description"] == "hello"
    assert request["Invoice"] == "INV-9"
    assert request["ReturnURL"] == "https://example.com/ok"
    assert request["ReturnURLCancel"] == "https://example.com/cancel"
    assert request["ReturnURLError"] == "https://example.com/error"
    assert request["ReturnURLReject"] == "https://example.com/reject"
    assert request["ContinueOnIncomplete"] == "0"
    assert request["PushURL"] == "https://example.com/push"
    assert request["PushURLFailure"] == "https://example.com/push-fail"
    assert request["ClientIP"] == {"Type": 0, "Address": "198.51.100.9"}


def test_from_dict_client_ip_as_dict_uses_address_and_type():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.from_dict({"client_ip": {"address": "203.0.113.5", "type": 1}})
    request = builder.build(validate=False).to_dict()
    assert request["ClientIP"] == {"Type": 1, "Address": "203.0.113.5"}


def test_from_dict_client_ip_empty_dict_uses_defaults():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.from_dict({"client_ip": {}})
    request = builder.build(validate=False).to_dict()
    assert request["ClientIP"] == {"Type": 0, "Address": "0.0.0.0"}


def test_from_dict_service_parameters_top_level_scalar_becomes_flat_parameter():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.from_dict({"service_parameters": {"issuer": "INGBNL2A"}})
    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert service["Parameters"] == [
        {"Name": "Issuer", "GroupType": "", "GroupID": "", "Value": "INGBNL2A"}
    ]


def test_from_dict_service_parameters_nested_dict_becomes_grouped_parameters():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.from_dict(
        {"service_parameters": {"customer": {"firstName": "Jane"}}}
    )
    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert service["Parameters"] == [
        {"Name": "Firstname", "GroupType": "Customer", "GroupID": "", "Value": "Jane"}
    ]


def test_from_dict_ignores_client_ip_of_unsupported_type():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    builder.from_dict({"client_ip": 12345})
    request = builder.build(validate=False).to_dict()
    # Falls through to PaymentRequest's default.
    assert request["ClientIP"] == {"Type": 0, "Address": "0.0.0.0"}


# ---------------------------------------------------------------------------
# _validate_required_fields


def test_build_raises_when_required_core_field_missing():
    builder = make_test_builder(object()).currency("EUR")  # missing everything else
    with pytest.raises(ValueError, match="Missing required fields"):
        builder.build(validate=False)


# ---------------------------------------------------------------------------
# refund


def test_refund_requires_original_transaction_key():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    with pytest.raises(ValueError, match="Original transaction key is required"):
        builder.refund()


def test_refund_full_swaps_debit_to_credit_and_adds_transaction_key():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "R-1"})
    )
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-123"})

    builder.refund(validate=False)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "TXN-123"
    assert sent["AmountCredit"] == 10.50
    assert "AmountDebit" not in sent
    mock.assert_all_consumed()


def test_refund_full_without_amount_debit_skips_swap():
    """Covers the ``if 'AmountDebit' in request_data`` False branch on the full-refund path."""
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "R-F"})
    )
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-X"})
    strip_amount_debit_from_build(builder)

    builder.refund(validate=False)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "TXN-X"
    assert "AmountDebit" not in sent
    assert "AmountCredit" not in sent
    mock.assert_all_consumed()


def test_refund_partial_without_amount_debit_skips_delete():
    """Covers the partial-refund ``if 'AmountDebit' in request_data`` False branch."""
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "R-P"})
    )
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict(
        {"original_transaction_key": "TXN-Y", "refund_amount": 2.5}
    )
    strip_amount_debit_from_build(builder)

    builder.refund(validate=False)

    sent = recorded_request(mock)
    assert sent["AmountCredit"] == 2.5
    assert "AmountDebit" not in sent
    mock.assert_all_consumed()


def test_refund_partial_uses_refund_amount_and_removes_debit():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "R-1"})
    )
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict(
        {"original_transaction_key": "TXN-9", "refund_amount": 3.25}
    )

    builder.refund(validate=False)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "TXN-9"
    assert sent["AmountCredit"] == 3.25
    assert "AmountDebit" not in sent
    mock.assert_all_consumed()


# ---------------------------------------------------------------------------
# capture


def test_capture_requires_authorization_key():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    with pytest.raises(ValueError, match="Authorization key is required"):
        builder.capture()


def test_capture_uses_key_argument_and_sets_original_transaction_key():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)

    builder.capture(original_transaction_key="AUTH-1", amount=4.0, validate=False)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "AUTH-1"
    assert sent["AmountDebit"] == 4.0
    mock.assert_all_consumed()


def test_capture_reads_authorization_key_and_amount_from_payload():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict({"authorization_key": "AUTH-2", "capture_amount": 7.5})

    builder.capture(validate=False)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "AUTH-2"
    assert sent["AmountDebit"] == 7.5
    mock.assert_all_consumed()


def test_capture_without_amount_argument_or_payload_keeps_built_amount():
    """Covers the ``if capture_amount is not None`` False branch."""
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict({"original_transaction_key": "AUTH-X"})

    builder.capture(validate=False)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "AUTH-X"
    # Amount stays as the built value from populate_required_fields.
    assert sent["AmountDebit"] == 10.50
    mock.assert_all_consumed()


# ---------------------------------------------------------------------------
# cancel


def test_cancel_requires_transaction_key():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    with pytest.raises(ValueError, match="Transaction key is required"):
        builder.cancel()


def test_cancel_removes_amounts_and_sets_transaction_key():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)

    builder.cancel(original_transaction_key="CANCEL-1")

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "CANCEL-1"
    assert "AmountDebit" not in sent
    assert "AmountCredit" not in sent
    mock.assert_all_consumed()


def test_cancel_reads_transaction_key_from_payload():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict({"cancel_key": "CANCEL-2"})

    builder.cancel()

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "CANCEL-2"
    mock.assert_all_consumed()


# ---------------------------------------------------------------------------
# partial_refund — has a known bug, pinned as regression


def test_partial_refund_raises_when_amount_missing_or_non_positive():
    builder = populate_required_fields(make_test_builder(object()), amount=10.50)
    with pytest.raises(ValueError, match="Partial refund amount must be greater than 0"):
        builder.partial_refund()


def test_partial_refund_reads_original_transaction_key_from_payload():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-1"})

    builder.partial_refund(amount=2.5)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "TXN-1"
    assert sent["AmountCredit"] == 2.5
    assert "AmountDebit" not in sent


def test_partial_refund_uses_explicit_original_transaction_key_argument():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)

    builder.partial_refund(original_transaction_key="TXN-2", amount=3.75)

    sent = recorded_request(mock)
    assert sent["OriginalTransactionKey"] == "TXN-2"
    assert sent["AmountCredit"] == 3.75
    assert "AmountDebit" not in sent


def test_partial_refund_does_not_leak_state_into_subsequent_full_refund():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "p"}))
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "f"}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)

    builder.partial_refund(original_transaction_key="TXN-A", amount=2.5)
    builder.from_dict({"original_transaction_key": "TXN-B"})
    builder.refund()

    assert json.loads(mock.calls[0]["data"])["AmountCredit"] == 2.5
    full = json.loads(mock.calls[1]["data"])
    assert full["OriginalTransactionKey"] == "TXN-B"
    assert full["AmountCredit"] == 10.50


def test_partial_refund_restores_pre_existing_payload_keys():
    mock, client = wire_recording_http()
    mock.queue(BuckarooMockRequest.json("POST", "*/json/transaction*", {"Key": "ok"}))
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-orig", "refund_amount": 9.99})

    builder.partial_refund(original_transaction_key="TXN-tmp", amount=2.5)

    assert builder._payload["original_transaction_key"] == "TXN-orig"
    assert builder._payload["refund_amount"] == 9.99


# ---------------------------------------------------------------------------
# _post_data_request and _post_transaction None-response branch


def test_post_data_request_posts_to_data_request_endpoint_and_parses_response():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json("POST", "*/json/DataRequest*", {"Key": "D-1"})
    )
    builder = populate_required_fields(make_test_builder(client), amount=10.50)
    request_data = builder.build(validate=False).to_dict()

    response = builder._post_data_request(request_data)

    assert "/json/DataRequest" in mock.calls[0]["url"]
    assert response.key == "D-1"
    mock.assert_all_consumed()


def _patch_http_client_post_returning(client, value):
    """Monkey-patch ``client.http_client.post`` to return ``value``."""
    client.http_client.post = lambda path, data: value


def test_post_transaction_returns_empty_payment_response_when_client_returns_none():
    _, client = wire_recording_http()
    _patch_http_client_post_returning(client, None)
    builder = populate_required_fields(make_test_builder(client), amount=10.50)

    response = builder._post_transaction({"anything": True})

    # Empty PaymentResponse wraps {}; nothing parsed from data.
    assert response.key is None
    assert response.to_dict() == {}


def test_post_data_request_returns_empty_payment_response_when_client_returns_none():
    _, client = wire_recording_http()
    _patch_http_client_post_returning(client, None)
    builder = populate_required_fields(make_test_builder(client), amount=10.50)

    response = builder._post_data_request({"anything": True})

    assert response.key is None
    assert response.to_dict() == {}


# ---------------------------------------------------------------------------
# execute_action — generic action dispatcher


def test_execute_action_posts_with_requested_action_name():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST", "*/json/transaction*", {"Key": "X-1"}
        )
    )
    builder = populate_required_fields(make_test_builder(client), amount=10.50)

    response = builder.execute_action("DummyAction", validate=False)

    sent = recorded_request(mock)
    assert sent["Services"]["ServiceList"][0]["Action"] == "DummyAction"
    assert response.key == "X-1"
    mock.assert_all_consumed()
