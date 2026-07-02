"""Unit tests for :class:`In3Builder`.

Targets 100% line + branch coverage of
``buckaroo/builders/payments/in3_builder.py``.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.in3_builder import In3Builder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


def test_construction_with_client_succeeds(client):
    builder = In3Builder(client)
    assert isinstance(builder, In3Builder)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_in3(client):
    assert In3Builder(client).get_service_name() == "in3"


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = In3Builder(client)

    assert builder.get_allowed_service_parameters("Pay") == {
        "billingCustomer": {
            "type": list,
            "required": True,
            "description": "Billing customer information",
        },
        "shippingCustomer": {
            "type": list,
            "required": True,
            "description": "Shipping customer information",
        },
        "article": {
            "type": list,
            "required": True,
            "description": "IN3 articles",
        },
        "route": {
            "type": str,
            "required": False,
            "description": ("In3 acquirer route, e.g. 'abn_b2b' for ABN-AMRO Achteraf Betalen"),
        },
    }


def test_get_allowed_service_parameters_pay_allows_optional_route(client):
    allowed = In3Builder(client).get_allowed_service_parameters("Pay")

    assert "route" in allowed
    assert allowed["route"]["required"] is False


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = In3Builder(client)

    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert In3Builder(client).get_allowed_service_parameters(action) == {}


def test_build_pay_with_route_keeps_route_parameter(client):
    request = (
        populate_required_fields(In3Builder(client), amount=99.95)
        .add_parameter("billingCustomer", [{"Name": "John"}])
        .add_parameter("shippingCustomer", [{"Name": "John"}])
        .add_parameter("article", [{"Description": "Widget", "Quantity": 1}])
        .add_parameter("route", "abn_b2b")
        .build("Pay")
    )

    service = request.services.services[0]
    route_params = [p for p in service.parameters if p.name == "Route"]

    assert len(route_params) == 1
    assert route_params[0].value == "abn_b2b"


def test_build_pay_without_route_is_unchanged(client):
    request = (
        populate_required_fields(In3Builder(client), amount=99.95)
        .add_parameter("billingCustomer", [{"Name": "John"}])
        .add_parameter("shippingCustomer", [{"Name": "John"}])
        .add_parameter("article", [{"Description": "Widget", "Quantity": 1}])
        .build("Pay")
    )

    service = request.services.services[0]

    assert all(p.name != "Route" for p in service.parameters)


def test_pay_posts_transaction_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "in3-key-456", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(In3Builder(client), amount=99.95)
        .add_parameter("billingCustomer", [{"Name": "John"}])
        .add_parameter("shippingCustomer", [{"Name": "John"}])
        .add_parameter("article", [{"Description": "Widget", "Quantity": 1}])
        .pay()
    )

    assert response.key == "in3-key-456"
