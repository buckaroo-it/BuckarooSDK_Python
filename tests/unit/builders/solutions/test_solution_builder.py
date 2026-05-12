"""Unit tests for :class:`SolutionBuilder`.

Covers the shared :class:`BaseBuilder` fluent surface exposed via
``SolutionBuilder``, plus the solution-specific override of
``required_fields`` (solutions have none).
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from buckaroo.builders.solutions.solution_builder import SolutionBuilder


class _DummySolutionBuilder(SolutionBuilder):
    """Minimal concrete :class:`SolutionBuilder` for tests."""

    _serviceName = "dummysolution"

    def get_service_name(self) -> str:
        return "DummySolution"

    def get_allowed_service_parameters(self, action: str = "Pay") -> Dict[str, Any]:
        return {}


@pytest.fixture
def builder() -> _DummySolutionBuilder:
    return _DummySolutionBuilder(client=object())


def test_fluent_setters_return_self(builder: _DummySolutionBuilder) -> None:
    assert builder.currency("EUR") is builder
    assert builder.amount(12.5) is builder
    assert builder.description("desc") is builder
    assert builder.invoice("INV-1") is builder
    assert builder.return_url("https://x/return") is builder
    assert builder.return_url_cancel("https://x/cancel") is builder
    assert builder.return_url_error("https://x/error") is builder
    assert builder.return_url_reject("https://x/reject") is builder
    assert builder.continue_on_incomplete("0") is builder
    assert builder.push_url("https://x/push") is builder
    assert builder.push_url_failure("https://x/push-fail") is builder
    assert builder.client_ip("1.2.3.4") is builder
    assert builder.add_parameter("foo", "bar") is builder


def test_required_fields_is_empty_for_solutions(builder: _DummySolutionBuilder) -> None:
    assert builder.required_fields() == {}
    assert builder.required_fields("CreateSubscription") == {}


def test_build_without_any_fields_succeeds_for_solution(
    builder: _DummySolutionBuilder,
) -> None:
    """Solutions have no required fields; ``build()`` must not raise."""
    request = builder.build("CreateSubscription", validate=False)

    payload = request.to_dict()
    assert payload["Services"] == {
        "ServiceList": [
            {"Name": "DummySolution", "Action": "CreateSubscription"},
        ]
    }
    # Solution fields default to None but stay in top-level shape
    assert payload["Currency"] is None
    assert payload["AmountDebit"] is None
    assert payload["ContinueOnIncomplete"] == "1"


def test_from_dict_populates_same_fields_as_payment_builders(
    builder: _DummySolutionBuilder,
) -> None:
    data = {
        "currency": "EUR",
        "amount": 42.0,
        "description": "subscription start",
        "invoice": "INV-9",
        "return_url": "https://x/return",
        "return_url_cancel": "https://x/cancel",
        "return_url_error": "https://x/error",
        "return_url_reject": "https://x/reject",
        "continue_on_incomplete": "0",
        "push_url": "https://x/push",
        "push_url_failure": "https://x/push-fail",
        "client_ip": {"address": "9.9.9.9", "type": 1},
        "service_parameters": {
            "flat": "1",
            "grouped": {"sub": "value"},
        },
    }

    assert builder.from_dict(data) is builder

    request = builder.build("CreateSubscription", validate=False)
    payload = request.to_dict()

    assert payload["Currency"] == "EUR"
    assert payload["AmountDebit"] == 42.0
    assert payload["Description"] == "subscription start"
    assert payload["Invoice"] == "INV-9"
    assert payload["ReturnURL"] == "https://x/return"
    assert payload["ReturnURLCancel"] == "https://x/cancel"
    assert payload["ReturnURLError"] == "https://x/error"
    assert payload["ReturnURLReject"] == "https://x/reject"
    assert payload["ContinueOnIncomplete"] == "0"
    assert payload["PushURL"] == "https://x/push"
    assert payload["PushURLFailure"] == "https://x/push-fail"
    assert payload["ClientIP"] == {"Type": 1, "Address": "9.9.9.9"}

    service = payload["Services"]["ServiceList"][0]
    assert service["Name"] == "DummySolution"
    assert service["Action"] == "CreateSubscription"

    param_names = {p["Name"]: p for p in service["Parameters"]}
    assert param_names["Flat"]["Value"] == "1"
    assert param_names["Flat"]["GroupType"] == ""
    assert param_names["Sub"]["Value"] == "value"
    assert param_names["Sub"]["GroupType"] == "Grouped"


def test_build_emits_parameters_when_added(builder: _DummySolutionBuilder) -> None:
    builder.add_parameter("token", "abc123")
    request = builder.build("CreateSubscription", validate=False)

    service = request.to_dict()["Services"]["ServiceList"][0]
    assert service["Parameters"] == [
        {"Name": "Token", "GroupType": "", "GroupID": "", "Value": "abc123"},
    ]
