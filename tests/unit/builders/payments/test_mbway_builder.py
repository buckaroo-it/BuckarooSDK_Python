"""Per-builder unit tests for :class:`MBWayBuilder`.

Phase 7.23 — per-builder coverage. ``MBWayBuilder`` is a minimal subclass of
:class:`PaymentBuilder`: it overrides only :meth:`get_service_name` and
:meth:`get_allowed_service_parameters`, and mixes in no capability classes.
Unlike :class:`CreditcardBuilder`, it doesn't declare a ``_serviceName`` class
attribute — the authoritative service name lives on
``get_service_name()`` and is what these tests pin.
"""

from __future__ import annotations

import pytest

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
from buckaroo.builders.payments.mbway_builder import MBWayBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


@pytest.fixture
def builder(client):
    return MBWayBuilder(client)


# ---------------------------------------------------------------------------
# Construction


def test_construction_returns_payment_builder(builder):
    assert isinstance(builder, MBWayBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_construction_binds_client(builder, client):
    assert builder._client is client


# ---------------------------------------------------------------------------
# _serviceName — MBWayBuilder does NOT declare a class-level ``_serviceName``


def test_mbway_builder_does_not_declare_class_service_name_attribute():
    """Pin that MBWayBuilder leaves ``_serviceName`` undeclared on the class.

    Unlike :class:`CreditcardBuilder`, ``MBWayBuilder`` relies solely on
    ``get_service_name()``. If someone later adds the class attribute, this
    test fails and they must decide whether both surfaces should agree.
    """
    assert "_serviceName" not in MBWayBuilder.__dict__


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_mbway(builder):
    assert builder.get_service_name() == "MBWay"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every supported action


@pytest.mark.parametrize(
    "action",
    ["Pay", "Refund", "PayRemainder", "ExtraInfo", "UnknownAction"],
)
def test_get_allowed_service_parameters_returns_empty_dict_for_every_action(
    builder, action
):
    assert builder.get_allowed_service_parameters(action) == {}


def test_get_allowed_service_parameters_defaults_to_pay_and_returns_empty(builder):
    """Covers the ``action: str = "Pay"`` default-argument branch."""
    assert builder.get_allowed_service_parameters() == {}


# ---------------------------------------------------------------------------
# Capability mixin sanity — MBWay mixes in nothing


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
def test_mbway_builder_does_not_inherit_capability_mixin(capability):
    assert not issubclass(MBWayBuilder, capability), (
        f"MBWayBuilder unexpectedly inherits {capability.__name__}; "
        "MBWay does not support that capability per the SDK spec."
    )


def test_base_pay_method_present_and_callable(builder):
    assert hasattr(builder, "pay")
    assert callable(builder.pay)


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_end_to_end_through_mock_buckaroo(builder, mock_strategy):
    """pay() builds a Pay action against the MBWay service, sends it
    through the HTTP client, and returns a parsed PaymentResponse."""
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {
                "Key": "MBWAY-KEY",
                "Status": {"Code": {"Code": 190, "Description": "Success"}},
                "Services": [{"Name": "MBWay", "Action": "Pay"}],
            },
        )
    )

    response = (
        populate_required_fields(builder, amount=12.34)
        .pay()
    )

    assert response.key == "MBWAY-KEY"
    mock_strategy.assert_all_consumed()
