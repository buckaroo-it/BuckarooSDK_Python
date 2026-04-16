"""Unit coverage for :class:`SwishBuilder`.

SwishBuilder is a minimal subclass of :class:`PaymentBuilder`. It defines no
capability mixins and no class-level ``_serviceName``; the only overrides are
``get_service_name()`` and ``get_allowed_service_parameters()``. These tests
pin that surface and drive a ``pay()`` round-trip through :class:`MockBuckaroo`
to hit every branch in ``swish_builder.py``.
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
from buckaroo.builders.payments.swish_builder import SwishBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def mock_strategy() -> MockBuckaroo:
    return MockBuckaroo()


@pytest.fixture
def client(mock_strategy: MockBuckaroo) -> BuckarooClient:
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock_strategy
    return c


@pytest.fixture
def builder(client: BuckarooClient) -> SwishBuilder:
    return SwishBuilder(client)


# ---------------------------------------------------------------------------
# Construction


def test_construction_wires_client(builder: SwishBuilder, client: BuckarooClient) -> None:
    assert isinstance(builder, SwishBuilder)
    assert isinstance(builder, PaymentBuilder)
    assert builder._client is client


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_swish(builder: SwishBuilder) -> None:
    assert builder.get_service_name() == "Swish"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every branch


def test_get_allowed_service_parameters_pay_is_empty_dict(builder: SwishBuilder) -> None:
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_pay_is_case_insensitive(
    builder: SwishBuilder,
) -> None:
    assert builder.get_allowed_service_parameters("pay") == {}


def test_get_allowed_service_parameters_defaults_to_pay(builder: SwishBuilder) -> None:
    # Covers the ``action: str = "Pay"`` default-argument branch.
    assert builder.get_allowed_service_parameters() == {}


@pytest.mark.parametrize(
    "action", ["Refund", "Capture", "Authorize", "ExtraInfo", "UnknownAction"]
)
def test_get_allowed_service_parameters_non_pay_returns_empty_dict(
    builder: SwishBuilder, action: str
) -> None:
    assert builder.get_allowed_service_parameters(action) == {}


# ---------------------------------------------------------------------------
# Capability mixin sanity — Swish mixes in nothing


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
def test_swish_builder_does_not_inherit_capability_mixin(capability) -> None:
    assert not issubclass(SwishBuilder, capability), (
        f"SwishBuilder unexpectedly inherits {capability.__name__}; "
        "Swish does not support that capability per the SDK spec."
    )


def test_inherited_pay_is_present_and_callable(builder: SwishBuilder) -> None:
    assert hasattr(builder, "pay")
    assert callable(builder.pay)


def test_does_not_expose_capability_only_methods(builder: SwishBuilder) -> None:
    for method in (
        "authorize",
        "authorizeEncrypted",
        "cancelAuthorize",
        "payEncrypted",
        "instantRefund",
        "payFastCheckout",
    ):
        assert not hasattr(builder, method), (
            f"SwishBuilder unexpectedly exposes capability method {method!r}"
        )


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_transaction_and_parses_response(
    builder: SwishBuilder, mock_strategy: MockBuckaroo
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "swish-key-123", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        builder.currency("SEK")
        .amount(49.99)
        .description("Swish order")
        .invoice("INV-SWISH-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .pay()
    )

    assert response.key == "swish-key-123"
    assert response.status.code.code == 190
    mock_strategy.assert_all_consumed()
