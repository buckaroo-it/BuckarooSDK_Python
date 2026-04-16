"""Unit coverage for :class:`KnakenBuilder`.

Phase 7.22 — per-builder coverage. KnakenBuilder is a minimal subclass of
:class:`PaymentBuilder` that only overrides :meth:`get_service_name` and
:meth:`get_allowed_service_parameters`; it mixes in no capability classes.
Tests exercise every public surface and pin the allowed-parameter shape for
every action we care about.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
    AuthorizeCaptureCapable,
)
from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import (
    BankTransferCapabilities,
)
from buckaroo.builders.payments.capabilities.encrypted_pay_capable import (
    EncryptedPayCapable,
)
from buckaroo.builders.payments.capabilities.fast_checkout_capable import (
    FastCheckoutCapable,
)
from buckaroo.builders.payments.capabilities.instant_refund_capable import (
    InstantRefundCapable,
)
from buckaroo.builders.payments.knaken_builder import KnakenBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


@pytest.fixture
def client():
    """BuckarooClient with HTTP strategy swapped for a MockBuckaroo."""
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = MockBuckaroo()
    return c


# ---------------------------------------------------------------------------
# Construction


def test_construction_wired_to_mock_buckaroo_succeeds(client):
    builder = KnakenBuilder(client)

    assert isinstance(builder, KnakenBuilder)
    assert isinstance(builder, PaymentBuilder)


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_knaken(client):
    builder = KnakenBuilder(client)

    assert builder.get_service_name() == "Knaken"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every supported action


@pytest.mark.parametrize(
    "action",
    ["Pay", "Refund", "PayRemainder", "ExtraInfo", "UnknownAction"],
)
def test_get_allowed_service_parameters_returns_empty_dict_for_every_action(
    client, action
):
    builder = KnakenBuilder(client)

    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay_and_returns_empty(client):
    """Covers the ``action: str = "Pay"`` default-argument branch."""
    builder = KnakenBuilder(client)

    assert builder.get_allowed_service_parameters() == {}


# ---------------------------------------------------------------------------
# Capability mixin sanity — Knaken mixes in nothing


@pytest.mark.parametrize(
    "capability",
    [
        AuthorizeCaptureCapable,
        BankTransferCapabilities,
        EncryptedPayCapable,
        FastCheckoutCapable,
        InstantRefundCapable,
    ],
    ids=lambda c: c.__name__,
)
def test_knaken_builder_does_not_inherit_capability_mixin(capability):
    assert not issubclass(KnakenBuilder, capability), (
        f"KnakenBuilder unexpectedly inherits {capability.__name__}; "
        "Knaken does not support that capability per the SDK spec."
    )


# ---------------------------------------------------------------------------
# Base-class actions present and callable (hasattr + callable sanity)


@pytest.mark.parametrize("method", ["pay", "refund"])
def test_base_builder_action_is_present_and_callable(client, method):
    builder = KnakenBuilder(client)

    assert hasattr(builder, method)
    assert callable(getattr(builder, method))


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_knaken_service_to_transaction_endpoint_and_parses_response():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "KNK-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = populate_required_fields(KnakenBuilder(client), amount=42.50)

    response = builder.pay(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "Knaken"
    assert service["Action"] == "Pay"
    assert response.key == "KNK-1"
    mock.assert_all_consumed()
