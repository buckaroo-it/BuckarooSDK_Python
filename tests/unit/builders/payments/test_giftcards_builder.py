"""Per-builder unit tests for :class:`GiftcardsBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for every
``giftcard_name`` branch, empty-payload default fallback, and a ``pay()``
dispatch through ``MockBuckaroo``.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.giftcards_builder import GiftcardsBuilder, INTERSOLVE_BRANDS
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_request, wire_recording_http


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = GiftcardsBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_class_does_not_declare_service_name_attribute():
    """Unlike ``CreditcardBuilder``, ``GiftcardsBuilder`` does not set
    ``_serviceName`` on the class — service name is derived dynamically from
    ``_payload['giftcard_name']`` with a ``'giftcards'`` default.
    """
    assert not hasattr(GiftcardsBuilder, "_serviceName")


# Buckaroo rejects the capitalized "Giftcards" with 491 'is not a valid service
# name'. The umbrella selectable-services flow uses lowercase ``giftcards``.
def test_get_service_name_defaults_to_giftcards_when_payload_empty(client):
    assert GiftcardsBuilder(client).get_service_name() == "giftcards"


def test_get_service_name_reads_giftcard_name_from_payload(client):
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "fashioncheque"})
    assert builder.get_service_name() == "fashioncheque"


def test_get_allowed_service_parameters_empty_payload_returns_empty_for_redirect_mode(client):
    """Redirect mode: when no ``giftcard_name`` is set, Buckaroo's hosted page
    collects card details so the SDK must not require any parameters locally.
    """
    builder = GiftcardsBuilder(client)
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_pay_succeeds_in_redirect_mode_without_card_details():
    """Redirect mode constructs a payload with no Cardnumber/PIN but does set
    ``services_selectable_by_client``. The validator must not raise.
    """
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "GC-REDIRECT-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(GiftcardsBuilder(client), amount=10.50)
    builder.services_selectable_by_client("fashioncheque,intersolve,tcs")

    response = builder.pay()

    assert response.key == "GC-REDIRECT-1"
    mock.assert_all_consumed()


def test_get_allowed_service_parameters_pay_fashioncheque_snapshot(client):
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "fashioncheque"})
    assert builder.get_allowed_service_parameters("Pay") == {
        "FashionChequeCardNumber": {
            "type": str,
            "required": True,
            "description": "Save payment token for future use",
        },
        "FashionChequePIN": {
            "type": str,
            "required": True,
            "description": "Save payment token for future use",
        },
    }


def test_get_allowed_service_parameters_pay_intersolve_snapshot(client):
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "intersolve"})
    assert builder.get_allowed_service_parameters("Pay") == {
        "IntersolveCardnumber": {"type": str, "required": True, "description": ""},
        "IntersolvePIN": {"type": str, "required": True, "description": ""},
    }


@pytest.mark.parametrize(
    "brand", ["intersolve", "vvvgiftcard", "webshopgiftcard", "boekenbon", "yourgift"]
)
def test_get_allowed_service_parameters_intersolve_backed_brands_use_intersolve_params(
    client, brand
):
    """VVV, webshop, boekenbon, yourgift all run on the Intersolve backend.
    The gateway expects ``IntersolveCardnumber``/``IntersolvePIN`` for them —
    not the generic ``Cardnumber``/``PIN`` pair (which the gateway rejects)."""
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": brand})
    assert builder.get_allowed_service_parameters("Pay") == {
        "IntersolveCardnumber": {"type": str, "required": True, "description": ""},
        "IntersolvePIN": {"type": str, "required": True, "description": ""},
    }


def test_get_allowed_service_parameters_pay_tcs_snapshot(client):
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "tcs"})
    assert builder.get_allowed_service_parameters("Pay") == {
        "TCSCardnumber": {"type": str, "required": True, "description": ""},
        "TCSValidationCode": {"type": str, "required": True, "description": ""},
    }


def test_get_allowed_service_parameters_pay_default_branch_snapshot(client):
    """Unknown ``giftcard_name`` values fall through to the generic spec."""
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "other"})
    assert builder.get_allowed_service_parameters("Pay") == {
        "Cardnumber": {"type": str, "required": True, "description": ""},
        "PIN": {"type": str, "required": True, "description": ""},
        "LastName": {"type": str, "required": False, "description": ""},
        "Email": {"type": str, "required": False, "description": ""},
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action; ``'pay'`` and ``'Pay'`` must match."""
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "other"})
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    """Unsupported actions short-circuit to ``{}`` before the ``giftcard_name``
    branch, so the empty-payload bug does not fire here."""
    assert GiftcardsBuilder(client).get_allowed_service_parameters("Authorize") == {}


@pytest.mark.parametrize(
    "brand", ["intersolve", "vvvgiftcard", "webshopgiftcard", "boekenbon", "yourgift"]
)
def test_get_allowed_service_parameters_refund_intersolve_brands_allow_lastname_email(
    client, brand
):
    """Intersolve giftcard refunds carry LastName + Email service params per
    Buckaroo docs (https://docs.buckaroo.io/docs/giftcards-integration
    #partial-refunds). LastName is required; Email is allowed-but-optional so a
    caller without one defers to Plaza's status 690 instead of a local raise."""
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": brand})
    assert builder.get_allowed_service_parameters("Refund") == {
        "LastName": {"type": str, "required": True, "description": ""},
        "Email": {"type": str, "required": False, "description": ""},
    }


def test_get_allowed_service_parameters_refund_non_intersolve_returns_empty(client):
    """Refund on fashioncheque / tcs / unknown brands carries no extra
    service params; only Intersolve-backed brands need LastName + Email."""
    for brand in ("fashioncheque", "tcs", "other", ""):
        builder = GiftcardsBuilder(client).from_dict({"giftcard_name": brand})
        assert builder.get_allowed_service_parameters("Refund") == {}


def test_refund_build_validates_when_intersolve_email_absent(client):
    """Regression: an Intersolve refund carrying LastName but no Email must
    build cleanly. Email is optional, so a missing one defers to Plaza's status
    690 instead of raising RequiredParameterMissingError during local validation.
    """
    builder = populate_required_fields(
        GiftcardsBuilder(client).from_dict({"giftcard_name": "vvvgiftcard"}),
        amount=10.50,
    )
    builder.add_parameter("LastName", "Customer")

    request = builder.build("Refund", validate=True)

    service = request.to_dict()["Services"]["ServiceList"][0]
    names = {p["Name"] for p in service["Parameters"]}
    assert "Lastname" in names
    assert "Email" not in names


def test_refund_build_keeps_intersolve_email_when_supplied(client):
    """A supplied Email must survive the refund filter — ``required: False``
    keeps the key allowed, it must not be stripped."""
    builder = populate_required_fields(
        GiftcardsBuilder(client).from_dict({"giftcard_name": "vvvgiftcard"}),
        amount=10.50,
    )
    builder.add_parameter("LastName", "Customer")
    builder.add_parameter("Email", "shopper@example.com")

    request = builder.build("Refund", validate=True)

    service = request.to_dict()["Services"]["ServiceList"][0]
    names = {p["Name"] for p in service["Parameters"]}
    assert {"Lastname", "Email"} <= names


def test_get_allowed_service_parameters_refund_is_case_insensitive(client):
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "intersolve"})
    assert builder.get_allowed_service_parameters("refund") == builder.get_allowed_service_parameters(
        "Refund"
    )


def test_pay_dispatches_giftcards_service_through_mock_buckaroo():
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "GC-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(GiftcardsBuilder(client), amount=10.50)
    builder.from_dict({"giftcard_name": "fashioncheque"})

    response = builder.pay(validate=False)

    assert response.key == "GC-1"
    mock.assert_all_consumed()


def test_intersolve_brands_constant_is_importable_and_correct():
    assert INTERSOLVE_BRANDS == frozenset(
        {"intersolve", "vvvgiftcard", "webshopgiftcard", "boekenbon", "yourgift"}
    )


def test_pay_redirect_omits_services_and_sends_selectable_by_client_csv():
    """Redirect mode: wire body must contain ServicesSelectableByClient and
    all core fields, but no Services entry — Buckaroo rejects giftcard service
    names so brand selection is delegated to the hosted page."""
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "GC-REDIRECT-2", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(GiftcardsBuilder(client), amount=10.50)
    builder.services_selectable_by_client("vvvgiftcard,boekenbon")

    response = builder.pay_redirect()

    sent = recorded_request(mock)
    assert "Services" not in sent
    assert sent["ServicesSelectableByClient"] == "vvvgiftcard,boekenbon"
    assert sent["Currency"] == "EUR"
    assert sent["AmountDebit"] == 10.50
    assert sent["Invoice"] == "INV-1"
    assert sent["ReturnURL"] == "https://ret.example/ok"
    assert response.key == "GC-REDIRECT-2"
    mock.assert_all_consumed()
