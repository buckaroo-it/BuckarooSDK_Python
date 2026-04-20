"""Unit coverage for :class:`SepaDirectDebitBuilder`.

Phase 7.30 — per-builder coverage. SepaDirectDebit is a minimal subclass of
:class:`PaymentBuilder` that only overrides :meth:`get_service_name` and
:meth:`get_allowed_service_parameters`; it mixes in no capability classes.

The Pay action exposes SEPA mandate-related parameters (``mandateReference``,
``mandateDate``, ``startRecurrent``, ``electronicSignature``) on top of the
usual customer account fields. Tests snapshot the full Pay spec inline and
explicitly verify the mandate fields are present.
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
from buckaroo.builders.payments.sepadirectdebit_builder import (
    SepaDirectDebitBuilder,
)
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http
from tests.support.builders import populate_required_fields


@pytest.fixture
def builder(client: BuckarooClient) -> SepaDirectDebitBuilder:
    return SepaDirectDebitBuilder(client)


# ---------------------------------------------------------------------------
# Construction


def test_instantiates_as_payment_builder(builder: SepaDirectDebitBuilder) -> None:
    assert isinstance(builder, SepaDirectDebitBuilder)
    assert isinstance(builder, PaymentBuilder)


def test_construction_binds_client(
    builder: SepaDirectDebitBuilder, client: BuckarooClient
) -> None:
    assert builder._client is client


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_sepadirectdebit(
    builder: SepaDirectDebitBuilder,
) -> None:
    assert builder.get_service_name() == "SepaDirectDebit"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — Pay action snapshot


def test_get_allowed_service_parameters_pay_snapshot(
    builder: SepaDirectDebitBuilder,
) -> None:
    # Full inline snapshot of the Pay spec. If any field's metadata changes
    # this test fails, forcing an explicit review of the SDK contract.
    assert builder.get_allowed_service_parameters("Pay") == {
        "customeraccountname": {
            "type": str,
            "required": True,
            "description": "Customer account name",
        },
        "customeriban": {
            "type": str,
            "required": True,
            "description": "Customer IBAN",
        },
        "customerbic": {
            "type": str,
            "required": False,
            "description": "Customer BIC",
        },
        "collectdate": {
            "type": str,
            "required": False,
            "description": "Collect date",
        },
        "mandateReference": {
            "type": str,
            "required": False,
            "description": "Mandate reference",
        },
        "mandateDate": {
            "type": str,
            "required": False,
            "description": "Mandate date",
        },
        "startRecurrent": {
            "type": str,
            "required": False,
            "description": "Start recurrent",
        },
        "electronicSignature": {
            "type": str,
            "required": False,
            "description": "Electronic signature",
        },
    }


def test_get_allowed_service_parameters_default_action_matches_pay(
    builder: SepaDirectDebitBuilder,
) -> None:
    # Covers the ``action: str = "Pay"`` default-argument branch.
    assert (
        builder.get_allowed_service_parameters()
        == builder.get_allowed_service_parameters("Pay")
    )


def test_get_allowed_service_parameters_pay_case_insensitive(
    builder: SepaDirectDebitBuilder,
) -> None:
    # The source branches on ``action.lower() in ["pay"]`` — pin lowercase too.
    assert (
        builder.get_allowed_service_parameters("pay")
        == builder.get_allowed_service_parameters("Pay")
    )


@pytest.mark.parametrize(
    "action",
    ["Refund", "Authorize", "Capture", "PayRemainder", "ExtraInfo", "Unknown"],
)
def test_get_allowed_service_parameters_non_pay_actions_return_empty(
    builder: SepaDirectDebitBuilder, action: str
) -> None:
    # Source returns ``{}`` for every action except Pay; snapshot the
    # non-Pay branch so a future per-action table doesn't silently regress.
    assert builder.get_allowed_service_parameters(action) == {}


# ---------------------------------------------------------------------------
# Capability mixin sanity — SepaDirectDebit mixes in nothing


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
def test_sepadirectdebit_builder_does_not_inherit_capability_mixin(capability):
    assert not issubclass(SepaDirectDebitBuilder, capability), (
        f"SepaDirectDebitBuilder unexpectedly inherits {capability.__name__}; "
        "SepaDirectDebit does not support that capability per the SDK spec."
    )


def test_has_inherited_pay_action_method(
    builder: SepaDirectDebitBuilder,
) -> None:
    # Only the inherited ``pay`` action is available; pin presence + callability
    # so a refactor of the base class that hides ``pay`` surfaces here.
    assert hasattr(builder, "pay")
    assert callable(builder.pay)


def test_does_not_mix_in_capability_methods(
    builder: SepaDirectDebitBuilder,
) -> None:
    for method in (
        "authorize",
        "authorizeEncrypted",
        "cancelAuthorize",
        "payEncrypted",
        "instantRefund",
        "payFastCheckout",
    ):
        assert not hasattr(builder, method), (
            f"SepaDirectDebitBuilder unexpectedly exposes capability method {method!r}"
        )


# ---------------------------------------------------------------------------
# End-to-end pay via MockBuckaroo


def test_pay_posts_sepadirectdebit_service_to_transaction_endpoint():
    mock, stub_client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "SDD-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = SepaDirectDebitBuilder(stub_client)
    populate_required_fields(builder, amount=12.34)

    response = builder.pay(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "SepaDirectDebit"
    assert service["Action"] == "Pay"
    assert response.key == "SDD-1"
    mock.assert_all_consumed()
