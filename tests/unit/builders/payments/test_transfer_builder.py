"""Unit coverage for :class:`TransferBuilder`.

Phase 7.33 — per-builder coverage. TransferBuilder is a minimal subclass of
:class:`PaymentBuilder`; it mixes in no capability classes and only overrides
:meth:`get_service_name` and :meth:`get_allowed_service_parameters`. Tests
snapshot the allowed-parameter shape for every action we care about and drive
one ``pay()`` round-trip through :class:`MockBuckaroo` for end-to-end coverage
of the inherited action path.
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
from buckaroo.builders.payments.transfer_builder import TransferBuilder
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
def builder(client: BuckarooClient) -> TransferBuilder:
    return TransferBuilder(client)


# ---------------------------------------------------------------------------
# Construction


def test_instantiates_as_payment_builder(builder: TransferBuilder) -> None:
    assert isinstance(builder, PaymentBuilder)
    assert isinstance(builder, TransferBuilder)


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_transfer(builder: TransferBuilder) -> None:
    assert builder.get_service_name() == "Transfer"


# ---------------------------------------------------------------------------
# _serviceName class attribute — TransferBuilder does NOT set one; the service
# identity is projected exclusively via get_service_name(). Pin that so a
# future refactor that introduces an out-of-sync class attribute trips here.


def test_service_name_class_attribute_not_set() -> None:
    # ``_serviceName`` is an optional class-level attribute some builders use
    # to declare the wire name. TransferBuilder relies solely on the
    # ``get_service_name()`` override, so the attribute is absent on the class
    # itself (it may exist on a distant ancestor — we only guard against
    # Transfer accidentally introducing a drifting copy).
    assert "_serviceName" not in TransferBuilder.__dict__


# ---------------------------------------------------------------------------
# get_allowed_service_parameters


def test_get_allowed_service_parameters_pay_snapshot(builder: TransferBuilder) -> None:
    spec = builder.get_allowed_service_parameters("Pay")
    assert "customeremail" in spec
    assert spec["customeremail"]["required"] is True
    assert "customerfirstname" in spec
    assert "customerlastname" in spec
    assert "customergender" in spec
    assert spec["customergender"]["required"] is False
    assert "sendmail" in spec
    assert spec["sendmail"]["required"] is False
    assert "dateDue" in spec
    assert spec["dateDue"]["required"] is False
    assert "customerCountry" in spec
    assert spec["customerCountry"]["required"] is False


def test_get_allowed_service_parameters_unsupported_action_returns_empty(
    builder: TransferBuilder,
) -> None:
    assert builder.get_allowed_service_parameters("Refund") == {}


def test_pay_dispatches_through_mock_buckaroo(
    mock_strategy: MockBuckaroo, client: BuckarooClient
) -> None:
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "transfer-key-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        TransferBuilder(client)
        .currency("EUR")
        .amount(25.00)
        .description("Transfer order")
        .invoice("INV-TRF-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .pay(validate=False)
    )

    assert response.key == "transfer-key-1"
    mock_strategy.assert_all_consumed()
