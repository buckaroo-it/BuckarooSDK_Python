"""Per-builder unit tests for :class:`ClickToPayBuilder`.

Covers the trivial per-builder surface: construction, service name, allowed
service parameters per action, capability sanity, and one end-to-end ``pay()``
round-trip through :class:`MockBuckaroo`.

``ClickToPayBuilder`` doesn't declare a ``_serviceName`` class attribute (unlike
:class:`CreditcardBuilder`); the authoritative service name is exposed via
``get_service_name()`` and is what gets asserted here.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.click_to_pay_builder import ClickToPayBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


@pytest.fixture
def builder(client):
    return ClickToPayBuilder(client)


def test_construction_returns_payment_builder(builder):
    assert isinstance(builder, PaymentBuilder)
    assert isinstance(builder, ClickToPayBuilder)


def test_get_service_name_returns_click_to_pay(builder):
    assert builder.get_service_name() == "ClickToPay"


def test_get_allowed_service_parameters_pay_is_empty(builder):
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_defaults_to_pay(builder):
    assert builder.get_allowed_service_parameters() == {}


def test_get_allowed_service_parameters_unknown_action_is_empty(builder):
    assert builder.get_allowed_service_parameters("Refund") == {}


def test_pay_end_to_end_through_mock_buckaroo(builder, mock_strategy):
    """pay() builds a Pay action against the ClickToPay service, sends it
    through the HTTP client, and returns a parsed PaymentResponse."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {
                "Key": "CTP-KEY",
                "Status": {"Code": {"Code": 190, "Description": "Success"}},
                "Services": [{"Name": "ClickToPay", "Action": "Pay"}],
            },
        )
    )

    response = (
        populate_required_fields(builder, amount=12.34)
        .pay()
    )

    assert response.key == "CTP-KEY"
    assert response.status.code.code == 190
    mock_strategy.assert_all_consumed()
