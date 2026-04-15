"""Tests for :class:`buckaroo.builders.base_builder.BaseBuilder`.

Exercises the base builder directly via a tiny concrete subclass — no
coupling to any real payment method and, importantly, no inheritance
from :class:`PaymentBuilder` (which shadows nearly every ``BaseBuilder``
method with an identical copy). Tests assert through the public API
(``PaymentRequest.to_dict()``, returned ``Parameter`` objects) rather
than private attributes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from buckaroo.builders.base_builder import BaseBuilder
from buckaroo.exceptions._parameter_validation_error import (
    ParameterValidationError,
)
from tests.support.builders import (
    populate_required_fields,
    strip_amount_debit_from_build,
)


# ---------------------------------------------------------------------------
# Helpers: concrete BaseBuilder subclass with no PaymentBuilder in the MRO.


class _ConcreteBaseBuilder(BaseBuilder):
    """Minimal concrete :class:`BaseBuilder` for testing its own code paths."""

    def __init__(
        self,
        client,
        *,
        service_name: str = "dummy",
        allowed_params: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(client)
        self._service_name = service_name
        self._allowed = allowed_params or {}

    def get_service_name(self) -> str:
        return self._service_name

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        return self._allowed.get(action, {})


def _core_allowed_params() -> dict:
    """Allowed params used by happy-path builds. Shape mirrors real builders."""
    return {
        "Pay": {
            "issuer": {"type": str, "required": False},
            "description": {"type": str, "required": False},
        },
        "Refund": {},
        "Capture": {},
        "DummyAction": {},
    }


# ``_ConcreteBaseBuilder`` extends :class:`BaseBuilder` directly so these tests
# hit the base-class methods; ``make_test_builder`` returns a
# :class:`PaymentBuilder` subclass, which would shadow nearly every method with
# an identical copy and mask base-class coverage.
def _make_builder(
    *,
    service_name: str = "dummy",
    allowed: Optional[Dict[str, Dict[str, Any]]] = None,
    client=None,
) -> _ConcreteBaseBuilder:
    return _ConcreteBaseBuilder(
        client or MagicMock(),
        service_name=service_name,
        allowed_params=allowed if allowed is not None else _core_allowed_params(),
    )


# ---------------------------------------------------------------------------
# Fluent setters: return self and populate the built request


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
def test_fluent_setter_returns_self(setter, value, dict_key):
    builder = _make_builder()
    result = getattr(builder, setter)(value)
    assert result is builder


@pytest.mark.parametrize("setter,value,dict_key", FLUENT_SETTERS)
def test_fluent_setter_is_reflected_in_built_request(setter, value, dict_key):
    builder = populate_required_fields(_make_builder(), amount=10.50)
    # Overwrite the one under test with the parametrized value.
    getattr(builder, setter)(value)
    request = builder.build(validate=False).to_dict()
    assert request[dict_key] == value


def test_client_ip_setter_returns_self_and_appears_in_request():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    result = builder.client_ip("203.0.113.7", ip_type=1)
    assert result is builder

    request = builder.build(validate=False).to_dict()
    assert request["ClientIP"] == {"Type": 1, "Address": "203.0.113.7"}


def test_continue_on_incomplete_setter_returns_self_and_appears_in_request():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    assert builder.continue_on_incomplete("0") is builder
    request = builder.build(validate=False).to_dict()
    assert request["ContinueOnIncomplete"] == "0"


def test_push_url_setters_return_self_and_appear_in_request():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    assert builder.push_url("https://example.com/push") is builder
    assert (
        builder.push_url_failure("https://example.com/push-fail") is builder
    )
    request = builder.build(validate=False).to_dict()
    assert request["PushURL"] == "https://example.com/push"
    assert request["PushURLFailure"] == "https://example.com/push-fail"


# ---------------------------------------------------------------------------
# from_dict


def test_from_dict_populates_all_supported_core_fields_and_returns_self():
    builder = _make_builder()
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


def test_from_dict_client_ip_dict_form_uses_address_and_type():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.from_dict({"client_ip": {"address": "203.0.113.5", "type": 1}})
    request = builder.build(validate=False).to_dict()
    assert request["ClientIP"] == {"Type": 1, "Address": "203.0.113.5"}


def test_from_dict_client_ip_dict_form_uses_defaults_when_keys_missing():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.from_dict({"client_ip": {}})
    request = builder.build(validate=False).to_dict()
    assert request["ClientIP"] == {"Type": 0, "Address": "0.0.0.0"}


def test_from_dict_service_parameters_top_level_scalar():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.from_dict({"service_parameters": {"issuer": "INGBNL2A"}})
    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert service["Parameters"] == [
        {"Name": "Issuer", "GroupType": "", "GroupID": "", "Value": "INGBNL2A"}
    ]


def test_from_dict_service_parameters_nested_dict_becomes_grouped_parameters():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.from_dict(
        {"service_parameters": {"customer": {"firstName": "Jane"}}}
    )
    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert service["Parameters"] == [
        {
            "Name": "Firstname",
            "GroupType": "Customer",
            "GroupID": "",
            "Value": "Jane",
        }
    ]


def test_from_dict_ignores_unknown_field_silently():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.from_dict({"unknown_field": "surprise", "another_mystery": 123})
    request = builder.build(validate=False).to_dict()

    assert request["Currency"] == "EUR"
    serialized = str(request)
    assert "unknown_field" not in serialized
    assert "surprise" not in serialized


# ---------------------------------------------------------------------------
# add_parameter


def test_add_parameter_flat_capitalizes_name_and_stringifies_value():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    result = builder.add_parameter("issuer", "INGBNL2A")
    assert result is builder

    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert service["Parameters"] == [
        {
            "Name": "Issuer",
            "GroupType": "",
            "GroupID": "",
            "Value": "INGBNL2A",
        }
    ]


def test_add_parameter_grouped_sets_group_type_and_group_id():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.add_parameter(
        "firstName", "Jane", group_type="customer", group_id="7"
    )

    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert service["Parameters"] == [
        {
            "Name": "Firstname",
            "GroupType": "Customer",
            "GroupID": "7",
            "Value": "Jane",
        }
    ]


def test_add_parameter_boolean_values_are_lowercased_strings():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.add_parameter("enabled", True)
    builder.add_parameter("disabled", False)

    request = builder.build(validate=False).to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]
    assert params[0]["Value"] == "true"
    assert params[1]["Value"] == "false"


def test_add_parameter_twice_same_name_appends_both_entries():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.add_parameter("issuer", "first")
    builder.add_parameter("issuer", "second")

    request = builder.build(validate=False).to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]
    # Current documented behavior: both entries are appended; no dedup.
    assert len(params) == 2
    assert [p["Value"] for p in params] == ["first", "second"]


def test_add_parameter_with_list_of_dicts_adds_grouped_batch():
    builder = populate_required_fields(_make_builder(), amount=10.50)
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
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.add_parameter("articles", ["not-a-dict", 42])

    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert "Parameters" not in service


# ---------------------------------------------------------------------------
# _validate_and_filter_service_parameters


def test_validate_and_filter_drops_non_allowed_parameters():
    builder = populate_required_fields(
        _make_builder(allowed={"Pay": {"issuer": {"type": str, "required": False}}}),
        amount=10.50,
    )
    builder.add_parameter("issuer", "INGBNL2A")
    builder.add_parameter("rogue", "should-vanish")

    # build() runs the filter by default.
    request = builder.build().to_dict()
    params = request["Services"]["ServiceList"][0]["Parameters"]

    names = [p["Name"] for p in params]
    assert "Issuer" in names
    assert "Rogue" not in names


# ---------------------------------------------------------------------------
# build() — ClientIP defaulting and service parameters wiring


def test_build_defaults_client_ip_when_unset():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    request = builder.build(validate=False).to_dict()
    assert request["ClientIP"] == {"Type": 0, "Address": "0.0.0.0"}


def test_build_without_service_parameters_omits_parameters_key():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    request = builder.build(validate=False).to_dict()
    service = request["Services"]["ServiceList"][0]
    assert service["Name"] == "dummy"
    assert service["Action"] == "Pay"
    assert "Parameters" not in service


def test_build_uses_requested_action_name():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    request = builder.build(action="Refund", validate=False).to_dict()
    assert request["Services"]["ServiceList"][0]["Action"] == "Refund"


def test_build_raises_when_required_field_missing():
    builder = _make_builder().currency("EUR")  # missing everything else
    with pytest.raises(ValueError, match="Missing required fields"):
        builder.build(validate=False)


# ---------------------------------------------------------------------------
# Validator convenience passthroughs


def test_is_parameter_allowed_delegates_to_validator():
    builder = _make_builder(
        allowed={"Pay": {"issuer": {"type": str, "required": False}}}
    )
    assert builder.is_parameter_allowed("issuer", "Pay") is True
    assert builder.is_parameter_allowed("nope", "Pay") is False


def test_get_parameter_info_returns_allowed_params_for_action():
    allowed = {"Pay": {"issuer": {"type": str, "required": False}}}
    builder = _make_builder(allowed=allowed)
    assert builder.get_parameter_info("Pay") == allowed["Pay"]


def test_get_normalized_parameter_name_returns_canonical_name():
    builder = _make_builder(
        allowed={"Pay": {"issuer": {"type": str, "required": False}}}
    )
    assert builder.get_normalized_parameter_name("Issuer", "Pay") == "issuer"
    assert builder.get_normalized_parameter_name("unknown", "Pay") == ""


# ---------------------------------------------------------------------------
# required_fields


def test_required_fields_reflects_current_setter_state():
    builder = _make_builder().currency("EUR").amount(5.0)
    fields = builder.required_fields()
    assert fields["currency"] == "EUR"
    assert fields["amount_debit"] == 5.0
    assert fields["description"] is None


# ---------------------------------------------------------------------------
# pay / refund / capture / cancel / execute_action / partial_refund /
# _post_data_request / _post_transaction


class _StubResponse:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class _StubHttp:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, path, data):
        self.calls.append((path, data))
        return self.response


class _StubClient:
    def __init__(self, http_client):
        self.http_client = http_client


def _client_returning(response_payload):
    http = _StubHttp(_StubResponse(response_payload) if response_payload is not None else None)
    return _StubClient(http), http


def test_pay_posts_to_transaction_and_returns_payment_response():
    client, http = _client_returning({"Status": {"Code": {"Code": 190}}})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    response = builder.pay()

    assert http.calls[0][0] == "/json/transaction"
    assert response.to_dict()["Status"]["Code"]["Code"] == 190


def test_post_transaction_returns_empty_response_when_strategy_returns_none():
    client, http = _client_returning(None)
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    response = builder.pay()

    assert response.to_dict() == {}


def test_post_data_request_posts_to_data_request_path():
    client, http = _client_returning({"ok": True})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    request_data = builder.build(validate=False).to_dict()
    response = builder._post_data_request(request_data)

    assert http.calls[0][0] == "/json/DataRequest"
    assert response.to_dict() == {"ok": True}


def test_post_data_request_returns_empty_response_when_strategy_returns_none():
    client, http = _client_returning(None)
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    response = builder._post_data_request({"anything": True})
    assert response.to_dict() == {}


def test_refund_requires_original_transaction_key():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    with pytest.raises(ValueError, match="Original transaction key is required"):
        builder.refund()


def test_refund_full_swaps_debit_to_credit_and_adds_transaction_key():
    client, http = _client_returning({"Status": "ok"})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-123"})

    builder.refund()

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "TXN-123"
    assert sent["AmountCredit"] == 10.50
    assert "AmountDebit" not in sent


def test_refund_partial_uses_refund_amount_and_removes_debit():
    client, http = _client_returning({"Status": "ok"})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict(
        {"original_transaction_key": "TXN-9", "refund_amount": 3.25}
    )

    builder.refund()

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "TXN-9"
    assert sent["AmountCredit"] == 3.25
    assert "AmountDebit" not in sent


def test_capture_requires_authorization_key():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    with pytest.raises(ValueError, match="Authorization key is required"):
        builder.capture()


def test_capture_uses_key_argument_and_sets_original_transaction_key():
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    builder.capture(original_transaction_key="AUTH-1", amount=4.0)

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "AUTH-1"
    assert sent["AmountDebit"] == 4.0


def test_capture_reads_authorization_key_from_payload():
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict(
        {"authorization_key": "AUTH-2", "capture_amount": 7.5}
    )

    builder.capture()

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "AUTH-2"
    assert sent["AmountDebit"] == 7.5


def test_capture_reads_original_transaction_key_from_payload_fallback():
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict({"original_transaction_key": "AUTH-3"})

    builder.capture()

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "AUTH-3"


def test_cancel_requires_transaction_key():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    with pytest.raises(ValueError, match="Transaction key is required"):
        builder.cancel()


def test_cancel_removes_amounts_and_sets_transaction_key():
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    builder.cancel(original_transaction_key="CANCEL-1")

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "CANCEL-1"
    assert "AmountDebit" not in sent
    assert "AmountCredit" not in sent


def test_cancel_reads_cancel_key_from_payload():
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict({"cancel_key": "CANCEL-2"})

    builder.cancel()

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "CANCEL-2"


def test_cancel_reads_original_transaction_key_from_payload_fallback():
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict({"original_transaction_key": "CANCEL-3"})

    builder.cancel()

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "CANCEL-3"


def test_partial_refund_raises_when_amount_missing_or_non_positive():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    with pytest.raises(ValueError, match="Partial refund amount must be greater than 0"):
        builder.partial_refund()

    builder2 = populate_required_fields(_make_builder(), amount=10.50)
    with pytest.raises(ValueError, match="Partial refund amount must be greater than 0"):
        builder2.partial_refund(amount=0)


def test_partial_refund_uses_explicit_original_transaction_key_argument():
    client, http = _client_returning({"Status": "ok"})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    builder.partial_refund(original_transaction_key="TXN-1", amount=2.5)

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "TXN-1"
    assert sent["AmountCredit"] == 2.5
    assert "AmountDebit" not in sent


def test_partial_refund_reads_original_transaction_key_from_payload():
    client, http = _client_returning({"Status": "ok"})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-2"})

    builder.partial_refund(amount=3.75)

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "TXN-2"
    assert sent["AmountCredit"] == 3.75
    assert "AmountDebit" not in sent


def test_partial_refund_does_not_leak_state_into_subsequent_full_refund():
    """A partial refund must not silently turn a later full refund into a partial."""
    client, http = _client_returning({"Status": "ok"})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    builder.partial_refund(original_transaction_key="TXN-A", amount=2.5)
    builder.from_dict({"original_transaction_key": "TXN-B"})
    builder.refund()

    _, partial_sent = http.calls[0]
    _, full_sent = http.calls[1]
    assert partial_sent["AmountCredit"] == 2.5
    assert full_sent["OriginalTransactionKey"] == "TXN-B"
    assert full_sent["AmountCredit"] == 10.50


def test_partial_refund_restores_pre_existing_payload_keys():
    """Pre-existing payload values for the stashed keys survive partial_refund."""
    client, http = _client_returning({"Status": "ok"})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-orig", "refund_amount": 9.99})

    builder.partial_refund(original_transaction_key="TXN-tmp", amount=2.5)

    assert builder._payload["original_transaction_key"] == "TXN-orig"
    assert builder._payload["refund_amount"] == 9.99


def test_execute_action_posts_with_requested_action():
    client, http = _client_returning({"done": True})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)

    response = builder.execute_action("DummyAction", validate=False)

    path, sent = http.calls[0]
    assert path == "/json/transaction"
    assert sent["Services"]["ServiceList"][0]["Action"] == "DummyAction"
    assert response.to_dict() == {"done": True}


def test_from_dict_ignores_client_ip_of_unsupported_type():
    builder = populate_required_fields(_make_builder(), amount=10.50)
    builder.from_dict({"client_ip": 12345})
    request = builder.build(validate=False).to_dict()
    # Falls through to PaymentRequest's default.
    assert request["ClientIP"] == {"Type": 0, "Address": "0.0.0.0"}


def test_refund_full_without_amount_debit_in_request_is_a_noop_swap():
    """Covers the ``else`` branch where ``AmountDebit`` was never in the dict."""
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict({"original_transaction_key": "TXN-X"})
    strip_amount_debit_from_build(builder)

    builder.refund()

    _, sent = http.calls[0]
    assert sent["OriginalTransactionKey"] == "TXN-X"
    assert "AmountDebit" not in sent
    assert "AmountCredit" not in sent


def test_refund_partial_without_amount_debit_in_request_skips_delete():
    """Covers the ``if 'AmountDebit' in request_data`` False branch on the partial path."""
    client, http = _client_returning({})
    builder = populate_required_fields(_make_builder(client=client), amount=10.50)
    builder.from_dict(
        {"original_transaction_key": "TXN-Y", "refund_amount": 2.5}
    )
    strip_amount_debit_from_build(builder)

    builder.refund()

    _, sent = http.calls[0]
    assert sent["AmountCredit"] == 2.5
    assert "AmountDebit" not in sent


def test_build_with_strict_validation_raises_on_unknown_parameter():
    builder = populate_required_fields(
        _make_builder(allowed={"Pay": {"issuer": {"type": str, "required": False}}}),
        amount=10.50,
    )
    builder.add_parameter("rogue", "x")

    with pytest.raises(ParameterValidationError):
        builder.build(strict_validation=True)


# ---------------------------------------------------------------------------
# Abstract-stub contract. These methods have no default behavior; a subclass
# that forgets to override them must fail loudly rather than return ``None``.


def test_get_service_name_stub_raises_not_implemented():
    builder = _make_builder()
    with pytest.raises(NotImplementedError):
        BaseBuilder.get_service_name(builder)


def test_get_allowed_service_parameters_stub_raises_not_implemented():
    builder = _make_builder()
    with pytest.raises(NotImplementedError):
        BaseBuilder.get_allowed_service_parameters(builder)
