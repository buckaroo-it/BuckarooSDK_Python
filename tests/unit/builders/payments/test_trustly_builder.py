"""Unit coverage for :class:`TrustlyBuilder`.

Phase 7.34 — per-builder coverage. ``TrustlyBuilder`` is a thin subclass of
:class:`PaymentBuilder` that only overrides :meth:`get_service_name` and
:meth:`get_allowed_service_parameters`; it mixes in no capability classes.
Tests pin every public surface and drive ``pay()`` end-to-end through
:class:`tests.support.mock_buckaroo.MockBuckaroo`.
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
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.builders.payments.trustly_builder import TrustlyBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


@pytest.fixture
def builder(client: BuckarooClient) -> TrustlyBuilder:
    return TrustlyBuilder(client)


# ---------------------------------------------------------------------------
# Construction


def test_construction_wired_to_mock_buckaroo_succeeds(client, builder):
    assert isinstance(builder, TrustlyBuilder)
    assert isinstance(builder, PaymentBuilder)
    assert builder._client is client


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_trustly(builder):
    assert builder.get_service_name() == "Trustly"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every supported action


def test_get_allowed_service_parameters_pay_snapshot(builder):
    assert builder.get_allowed_service_parameters("Pay") == {
        "customerFirstName": {
            "type": str,
            "required": True,
            "description": "Customer first name",
        },
        "customerLastName": {
            "type": str,
            "required": True,
            "description": "Customer last name",
        },
        "customerCountryCode": {
            "type": str,
            "required": True,
            "description": "Customer country code",
        },
        "consumeremail": {
            "type": str,
            "required": True,
            "description": "Customer email",
        },
    }


def test_get_allowed_service_parameters_pay_is_case_insensitive(builder):
    """Covers the ``action.lower()`` branch for lowercase input."""
    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


def test_get_allowed_service_parameters_defaults_to_pay(builder):
    """Covers the ``action: str = "Pay"`` default-argument branch."""
    assert builder.get_allowed_service_parameters() == (
        builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize(
    "action", ["Refund", "Capture", "Authorize", "ExtraInfo", "UnknownAction"]
)
def test_get_allowed_service_parameters_non_pay_returns_empty(builder, action):
    assert builder.get_allowed_service_parameters(action) == {}


# ---------------------------------------------------------------------------
# Capability mixin sanity — Trustly mixes in nothing


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
def test_trustly_builder_does_not_inherit_capability_mixin(capability):
    assert not issubclass(TrustlyBuilder, capability), (
        f"TrustlyBuilder unexpectedly inherits {capability.__name__}; "
        "Trustly does not support that capability per the SDK spec."
    )


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_trustly_service_to_transaction_endpoint_and_parses_response(
    client, mock_strategy
):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "trustly-key-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(TrustlyBuilder(client), amount=42.00)
        .add_parameter("customerFirstName", "Alice")
        .add_parameter("customerLastName", "Example")
        .add_parameter("customerCountryCode", "NL")
        .add_parameter("consumeremail", "alice@example.test")
        .pay()
    )

    assert response.key == "trustly-key-1"
    mock_strategy.assert_all_consumed()
