"""Per-builder unit tests for :class:`GiftcardsBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for every
``giftcard_name`` branch, empty-payload default fallback, and a ``pay()``
dispatch through ``MockBuckaroo``.
"""

from __future__ import annotations

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.giftcards_builder import GiftcardsBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = GiftcardsBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_class_does_not_declare_service_name_attribute():
    """Unlike ``CreditcardBuilder``, ``GiftcardsBuilder`` does not set
    ``_serviceName`` on the class — service name is derived dynamically from
    ``_payload['giftcard_name']`` with a ``'Giftcards'`` default.
    """
    assert not hasattr(GiftcardsBuilder, "_serviceName")


def test_get_service_name_defaults_to_giftcards_when_payload_empty(client):
    assert GiftcardsBuilder(client).get_service_name() == "Giftcards"


def test_get_service_name_reads_giftcard_name_from_payload(client):
    builder = GiftcardsBuilder(client).from_dict({"giftcard_name": "fashioncheque"})
    assert builder.get_service_name() == "fashioncheque"


def test_get_allowed_service_parameters_empty_payload_returns_default(client):
    builder = GiftcardsBuilder(client)
    spec = builder.get_allowed_service_parameters("Pay")
    assert "Cardnumber" in spec
    assert "PIN" in spec


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
    assert GiftcardsBuilder(client).get_allowed_service_parameters("Refund") == {}


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
