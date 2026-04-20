"""Per-builder unit tests for :class:`IdealQrBuilder`.

Covers construction, service-name shape, allowed-parameter snapshots for the
``Pay`` and ``Generate`` actions, required-fields override, and an end-to-end
``generate()`` dispatch through ``MockBuckaroo``. Phase 7.17.

The iDEAL QR builder only exposes parameters for the ``Generate`` action; the
default ``Pay`` path returns an empty dict from the override. ``generate()``
posts to ``/json/DataRequest`` rather than ``/json/transaction``.
"""

from __future__ import annotations

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.ideal_qr_builder import IdealQrBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = IdealQrBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_idealqr(client):
    assert IdealQrBuilder(client).get_service_name() == "IdealQr"


def test_get_allowed_service_parameters_pay_is_empty(client):
    """``Pay`` is not in the builder's action whitelist; the override returns {}."""
    assert IdealQrBuilder(client).get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_generate_snapshot(client):
    assert IdealQrBuilder(client).get_allowed_service_parameters("Generate") == {
        "amount": {
            "type": str,
            "required": True,
            "description": "iDEAL QR payment amount",
        },
        "amountIsChangeable": {
            "type": bool,
            "required": True,
            "description": "Indicates if the amount can be changed",
        },
        "purchaseId": {
            "type": str,
            "required": True,
            "description": "Unique purchase identifier",
        },
        "description": {
            "type": str,
            "required": True,
            "description": "Description of the payment",
        },
        "isOneOff": {
            "type": bool,
            "required": True,
            "description": "Indicates if the payment is a one-off",
        },
        "expiration": {
            "type": str,
            "required": True,
            "description": "Expiration time for the QR code",
        },
        "imageSize": {
            "type": str,
            "required": True,
            "description": "Size of the QR code image",
        },
        "isProcessing": {
            "type": bool,
            "required": False,
            "description": "Indicates if the payment is processing",
        },
        "minAmount": {
            "type": str,
            "required": False,
            "description": "Minimum amount allowed for the payment",
        },
        "maxAmount": {
            "type": str,
            "required": False,
            "description": "Maximum amount allowed for the payment",
        },
    }


def test_pay_and_generate_snapshots_are_distinct(client):
    builder = IdealQrBuilder(client)
    assert builder.get_allowed_service_parameters("Pay") != builder.get_allowed_service_parameters("Generate")


def test_get_allowed_service_parameters_is_case_insensitive_for_generate(client):
    """Source lower-cases the action before matching, so "generate" equals "Generate"."""
    builder = IdealQrBuilder(client)
    assert builder.get_allowed_service_parameters("generate") == builder.get_allowed_service_parameters("Generate")


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    assert IdealQrBuilder(client).get_allowed_service_parameters("Refund") == {}


def test_required_fields_omits_amount_debit(client):
    """IdealQr overrides ``required_fields`` to drop ``amount_debit`` since
    QR flows carry the amount in service parameters instead."""
    fields = IdealQrBuilder(client).required_fields("Pay")

    assert set(fields.keys()) == {
        "currency",
        "description",
        "invoice",
        "return_url",
        "return_url_cancel",
        "return_url_error",
        "return_url_reject",
    }


def test_required_fields_reflects_current_state(client):
    builder = IdealQrBuilder(client)
    builder.currency("EUR").description("desc").invoice("INV-1")
    builder.return_url("https://ret/ok")
    builder.return_url_cancel("https://ret/cancel")
    builder.return_url_error("https://ret/error")
    builder.return_url_reject("https://ret/reject")

    fields = builder.required_fields()
    assert fields["currency"] == "EUR"
    assert fields["description"] == "desc"
    assert fields["invoice"] == "INV-1"
    assert fields["return_url"] == "https://ret/ok"
    assert fields["return_url_cancel"] == "https://ret/cancel"
    assert fields["return_url_error"] == "https://ret/error"
    assert fields["return_url_reject"] == "https://ret/reject"


def test_generate_dispatches_through_mock_buckaroo():
    mock = MockBuckaroo()
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "qr-key-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    builder = IdealQrBuilder(c)
    builder.currency("EUR").description("QR").invoice("INV-QR-1")
    builder.return_url("https://ret/ok")
    builder.return_url_cancel("https://ret/cancel")
    builder.return_url_error("https://ret/error")
    builder.return_url_reject("https://ret/reject")

    response = builder.generate(validate=False)

    assert response.key == "qr-key-1"
    mock.assert_all_consumed()
