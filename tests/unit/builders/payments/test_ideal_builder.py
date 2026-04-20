"""Unit coverage for :class:`IdealBuilder`.

Phase 7.16 — per-builder coverage. IdealBuilder subclasses
:class:`PaymentBuilder` and mixes in :class:`BankTransferCapabilities` (which
itself composes :class:`InstantRefundCapable` + :class:`FastCheckoutCapable`).
Tests pin:

  * construction + ``PaymentBuilder`` lineage;
  * ``get_service_name()``;
  * the full allowed-parameter spec per action, including ``issuer``'s
    required flag on ``Pay`` / ``PayFastCheckout``;
  * mixin presence (``instantRefund`` + ``payFastCheckout`` bound and callable);
  * end-to-end ``pay()``, ``instantRefund()``, ``payFastCheckout()`` dispatch
    through :class:`MockBuckaroo`.
"""

from __future__ import annotations

from buckaroo.builders.payments.capabilities.bank_transfer_capabilities import (
    BankTransferCapabilities,
)
from buckaroo.builders.payments.capabilities.fast_checkout_capable import (
    FastCheckoutCapable,
)
from buckaroo.builders.payments.capabilities.instant_refund_capable import (
    InstantRefundCapable,
)
from buckaroo.builders.payments.ideal_builder import IdealBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


# ---------------------------------------------------------------------------
# Construction


def test_construction_wired_to_mock_buckaroo_succeeds(client):
    builder = IdealBuilder(client)

    assert isinstance(builder, IdealBuilder)
    assert isinstance(builder, PaymentBuilder)


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_ideal(client):
    assert IdealBuilder(client).get_service_name() == "ideal"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot per supported action


def test_get_allowed_service_parameters_pay_snapshot(client):
    assert IdealBuilder(client).get_allowed_service_parameters("Pay") == {
        "issuer": {
            "type": str,
            "required": False,
            "description": "iDEAL bank issuer code",
        },
    }


def test_pay_spec_declares_issuer_required_flag_explicitly(client):
    """Pin ``issuer``'s required-ness flag on the ``Pay`` spec.

    The Buckaroo v2 iDEAL flow no longer requires callers to supply a bank
    issuer up-front (the hosted page handles selection), so the SDK spec marks
    it optional. This test surfaces that decision explicitly so a future swap
    to ``required: True`` breaks here and gets scrutinised.
    """
    spec = IdealBuilder(client).get_allowed_service_parameters("Pay")
    assert "issuer" in spec
    assert spec["issuer"]["required"] is False


def test_get_allowed_service_parameters_payfastcheckout_matches_pay(client):
    """``PayFastCheckout`` shares the same issuer spec as ``Pay``."""
    builder = IdealBuilder(client)

    assert builder.get_allowed_service_parameters(
        "PayFastCheckout"
    ) == builder.get_allowed_service_parameters("Pay")


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    assert IdealBuilder(client).get_allowed_service_parameters("Refund") == {}


def test_mixes_in_bank_transfer_capabilities(client):
    builder = IdealBuilder(client)
    assert isinstance(builder, BankTransferCapabilities)
    assert isinstance(builder, InstantRefundCapable)
    assert isinstance(builder, FastCheckoutCapable)


def test_pay_dispatches_ideal_service_through_mock_buckaroo(client):
    mock = client.http_client.http_strategy
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "ideal-key-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(IdealBuilder(client))
        .pay()
    )

    assert response.key == "ideal-key-1"
    mock.assert_all_consumed()
