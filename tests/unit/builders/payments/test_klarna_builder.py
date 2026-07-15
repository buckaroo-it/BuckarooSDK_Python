"""Per-builder unit tests for :class:`KlarnaBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for every
supported action including the grouped article / line-item structure, the
mixin-free baseline (KlarnaBuilder composes no capability mixins despite the
docstring mention of "bank transfer capabilities"), and an end-to-end
``pay()`` dispatch through ``MockBuckaroo``. Phase 7.20.
"""

from __future__ import annotations

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.klarna_builder import KlarnaBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = KlarnaBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_klarna(client):
    assert KlarnaBuilder(client).get_service_name() == "klarna"


def test_get_allowed_service_parameters_pay_snapshot(client):
    """Pay-as-capture references the prior Reserve via ``dataRequestKey`` as a
    service parameter. Cart contents are reused server-side from the Reserve."""
    assert KlarnaBuilder(client).get_allowed_service_parameters("Pay") == {
        "dataRequestKey": {
            "type": str,
            "required": True,
            "description": "Key of the prior Klarna Reserve",
        },
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action before matching, so "pay" equals "Pay"."""
    builder = KlarnaBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )


def test_get_allowed_service_parameters_reserve_snapshot(client):
    """Reserve action drives the Klarna MOR hosted-page flow. Same required
    cart trio as Pay (billingCustomer, shippingCustomer, article) plus
    optional Klarna-specific keys (operatingCountry, pno, gender, locale)."""
    assert KlarnaBuilder(client).get_allowed_service_parameters("Reserve") == {
        "billingCustomer": {
            "type": list,
            "required": True,
            "description": "Billing customer information",
        },
        "shippingCustomer": {
            "type": list,
            "required": True,
            "description": "Shipping customer information",
        },
        "article": {
            "type": list,
            "required": True,
            "description": "Klarna articles",
        },
        "operatingCountry": {
            "type": str,
            "required": False,
            "description": "Operating country code",
        },
        "pno": {
            "type": str,
            "required": False,
            "description": "Personal identification number",
        },
        "gender": {
            "type": str,
            "required": False,
            "description": "Customer gender",
        },
        "locale": {
            "type": str,
            "required": False,
            "description": "Customer locale",
        },
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_reserve(client):
    builder = KlarnaBuilder(client)
    assert builder.get_allowed_service_parameters(
        "reserve"
    ) == builder.get_allowed_service_parameters("Reserve")


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    assert KlarnaBuilder(client).get_allowed_service_parameters("Refund") == {}


def test_pay_dispatches_klarna_service_through_mock_buckaroo():
    client = BuckarooClient("store_key", "secret_key", mode="test")
    mock = MockBuckaroo()
    client.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "KL-1", "Status": {"Code": {"Code": 190}}},
        )
    )

    builder = populate_required_fields(KlarnaBuilder(client), amount=49.95)

    response = builder.pay(validate=False)

    assert response.key == "KL-1"
    mock.assert_all_consumed()


def test_get_allowed_service_parameters_cancelreservation_is_empty(client):
    """CancelReservation only needs OriginalTransactionKey at request level."""
    assert KlarnaBuilder(client).get_allowed_service_parameters("CancelReservation") == {}
    assert KlarnaBuilder(client).get_allowed_service_parameters("cancelreservation") == {}


def test_cancel_reservation_requires_original_transaction_key(client):
    """Missing key raises ValueError, mirroring cancelAuthorize."""
    import pytest

    builder = populate_required_fields(KlarnaBuilder(client), amount=10.0)
    with pytest.raises(ValueError, match="Original transaction key is required"):
        builder.cancelReservation(original_transaction_key="")


def test_cancel_reservation_dispatches_action_with_original_transaction_key():
    """cancelReservation builds action="CancelReservation" with the key in payload."""
    from unittest.mock import MagicMock

    class _StubResponse:
        def to_dict(self):
            return {"Status": {"Code": {"Code": 190}}}

    captured = {}

    class _StubHttp:
        def post(self, path, data):
            captured["path"] = path
            captured["data"] = data
            return _StubResponse()

    stub_client = MagicMock()
    stub_client.http_client = _StubHttp()

    builder = populate_required_fields(KlarnaBuilder(stub_client), amount=49.95)
    response = builder.cancelReservation(original_transaction_key="RES-KEY-9")

    assert response.to_dict()["Status"]["Code"]["Code"] == 190
    assert captured["path"] == "/json/transaction"
    sent = captured["data"]
    assert sent["OriginalTransactionKey"] == "RES-KEY-9"
    assert sent["Services"]["ServiceList"][0]["Action"] == "CancelReservation"
