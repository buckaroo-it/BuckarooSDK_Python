"""Unit coverage for :class:`MultibancoBuilder`.

Phase 7.24 — per-builder coverage. MultibancoBuilder is a minimal subclass of
:class:`PaymentBuilder`. It only overrides :meth:`get_service_name` and
:meth:`get_allowed_service_parameters`; it mixes in no capability classes
and declares no ``_serviceName`` class attribute. Tests pin the public
surface and the allowed-parameter shape for every action we care about.
"""

from __future__ import annotations

import pytest

from buckaroo.builders.payments.multibanco_builder import MultibancoBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


# ---------------------------------------------------------------------------
# Construction


def test_construction_with_client_succeeds(client):
    builder = MultibancoBuilder(client)

    assert isinstance(builder, MultibancoBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_multibanco_builder_does_not_declare_service_name_class_attribute():
    """MultibancoBuilder relies on :meth:`get_service_name` — no ``_serviceName`` attr.

    Pin the stub shape so a future refactor that introduces ``_serviceName``
    has to update the assertion consciously.
    """
    assert "_serviceName" not in MultibancoBuilder.__dict__


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_multibanco(client):
    builder = MultibancoBuilder(client)

    assert builder.get_service_name() == "Multibanco"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every supported action


@pytest.mark.parametrize(
    "action",
    ["Pay", "Refund", "Capture", "Authorize", "UnknownAction"],
)
def test_get_allowed_service_parameters_returns_empty_dict_for_every_action(client, action):
    builder = MultibancoBuilder(client)

    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay_and_returns_empty(client):
    """Covers the ``action: str = "Pay"`` default-argument branch."""
    builder = MultibancoBuilder(client)

    assert builder.get_allowed_service_parameters() == {}


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_multibanco_service_to_transaction_endpoint_and_parses_response():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "MLB-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = populate_required_fields(MultibancoBuilder(client), amount=12.34)

    response = builder.pay(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "Multibanco"
    assert service["Action"] == "Pay"
    assert response.key == "MLB-1"
    mock.assert_all_consumed()
