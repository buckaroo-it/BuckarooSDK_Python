"""Per-builder unit tests for :class:`KlarnaBuilder`.

Klarna MOR no longer returns a reservation number: every follow-up action
(``CancelReservation``, ``UpdateReservation``, ``ExtendReservation``,
``AddShippingInfo``) is a DataRequest keyed on the Buckaroo ``DataRequestKey``
service parameter and posts to ``/json/DataRequest``. ``Pay``/``Refund`` remain
transaction requests. The source also narrows :meth:`required_fields` per
action so the DataRequest methods pass ``_validate_required_fields``.
"""

from __future__ import annotations

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.payments.klarna_builder import KlarnaBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_request, wire_recording_http


def test_construct_with_buckaroo_client_returns_payment_builder(client):
    builder = KlarnaBuilder(client)
    assert isinstance(builder, PaymentBuilder)


def test_get_service_name_returns_klarna(client):
    assert KlarnaBuilder(client).get_service_name() == "klarna"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters


def test_get_allowed_service_parameters_pay_snapshot(client):
    """Pay-as-capture references the prior Reserve via ``dataRequestKey`` and
    optionally carries partial-delivery articles and shipping details."""
    assert KlarnaBuilder(client).get_allowed_service_parameters("Pay") == {
        "dataRequestKey": {
            "type": str,
            "required": True,
            "description": "Key of the prior Klarna Reserve",
        },
        "article": {
            "type": list,
            "required": False,
            "description": "Articles to pay for on a partial delivery",
        },
        "shippingMethod": {
            "type": str,
            "required": False,
            "description": "Shipping method",
        },
        "company": {
            "type": str,
            "required": False,
            "description": "Shipping company name",
        },
        "trackingNumber": {
            "type": str,
            "required": False,
            "description": "Shipping tracking number",
        },
    }


def test_get_allowed_service_parameters_is_case_insensitive_for_pay(client):
    """Source lower-cases the action before matching, so "pay" equals "Pay"."""
    builder = KlarnaBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == builder.get_allowed_service_parameters(
        "Pay"
    )


def test_get_allowed_service_parameters_reserve_snapshot(client):
    """Reserve drives the Klarna MOR hosted-page flow. Per BPS docs only the
    article list and operatingCountry are mandatory; customer info is optional."""
    assert KlarnaBuilder(client).get_allowed_service_parameters("Reserve") == {
        "article": {
            "type": list,
            "required": True,
            "description": "Klarna articles",
        },
        "operatingCountry": {
            "type": str,
            "required": True,
            "description": "Operating country code",
        },
        "billingCustomer": {
            "type": list,
            "required": False,
            "description": "Billing customer information",
        },
        "shippingCustomer": {
            "type": list,
            "required": False,
            "description": "Shipping customer information",
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


def test_get_allowed_service_parameters_cancelreservation_requires_data_request_key(client):
    """CancelReservation and ExtendReservation only need the DataRequestKey."""
    expected = {
        "dataRequestKey": {
            "type": str,
            "required": True,
            "description": "Buckaroo data request key of the prior Reserve",
        },
    }
    builder = KlarnaBuilder(client)
    assert builder.get_allowed_service_parameters("CancelReservation") == expected
    assert builder.get_allowed_service_parameters("cancelreservation") == expected


def test_get_allowed_service_parameters_extendreservation_matches_cancel(client):
    builder = KlarnaBuilder(client)
    assert builder.get_allowed_service_parameters(
        "ExtendReservation"
    ) == builder.get_allowed_service_parameters("CancelReservation")


def test_get_allowed_service_parameters_updatereservation_snapshot(client):
    assert KlarnaBuilder(client).get_allowed_service_parameters("UpdateReservation") == {
        "dataRequestKey": {
            "type": str,
            "required": True,
            "description": "Buckaroo data request key of the prior Reserve",
        },
        "article": {
            "type": list,
            "required": False,
            "description": "Updated Klarna articles",
        },
        "shippingCustomer": {
            "type": list,
            "required": False,
            "description": "Updated shipping customer information",
        },
    }


def test_get_allowed_service_parameters_unsupported_action_returns_empty(client):
    # Refund carries no service params; AddShippingInfo is not a klarna action
    # (the gateway rejects it — shipping details ride on Pay).
    assert KlarnaBuilder(client).get_allowed_service_parameters("Refund") == {}
    assert KlarnaBuilder(client).get_allowed_service_parameters("AddShippingInfo") == {}


# ---------------------------------------------------------------------------
# required_fields override


class TestRequiredFields:
    def test_reserve_requires_currency_and_invoice(self, client):
        builder = KlarnaBuilder(client).currency("EUR").invoice("INV-1")
        assert builder.required_fields("Reserve") == {"currency": "EUR", "invoice": "INV-1"}

    def test_pay_requires_currency_amount_and_invoice(self, client):
        """The gateway rejects Pay without an invoice number."""
        builder = KlarnaBuilder(client).currency("EUR").amount(12.34).invoice("INV-9")
        assert builder.required_fields("Pay") == {
            "currency": "EUR",
            "amount_debit": 12.34,
            "invoice": "INV-9",
        }

    def test_data_request_actions_require_nothing(self, client):
        builder = KlarnaBuilder(client)
        assert builder.required_fields("CancelReservation") == {}
        assert builder.required_fields("UpdateReservation") == {}
        assert builder.required_fields("ExtendReservation") == {}

    def test_refund_falls_through_to_base(self, client):
        """Refund keeps the full base required-field set (like every builder)."""
        assert set(KlarnaBuilder(client).required_fields("Refund")) == {
            "currency",
            "amount_debit",
            "description",
            "invoice",
            "return_url",
            "return_url_cancel",
            "return_url_error",
            "return_url_reject",
        }


# ---------------------------------------------------------------------------
# Pay / Refund dispatch through the transaction endpoint


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


# ---------------------------------------------------------------------------
# DataRequest follow-up actions — post to /json/DataRequest with the action name


class TestReserve:
    def test_posts_reserve_to_data_request_endpoint(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KL-RES-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaBuilder(client).currency("EUR").invoice("INV-1")

        response = builder.reserve(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "Reserve"
        assert recorded_request(mock)["Services"]["ServiceList"][0]["Name"] == "klarna"
        assert response.key == "KL-RES-1"
        mock.assert_all_consumed()


class TestCancelReservation:
    def test_posts_cancel_reservation_to_data_request_without_original_key(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KL-CAN-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaBuilder(client)
        builder.add_parameter("dataRequestKey", "RES-DRK-1")

        response = builder.cancelReservation(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "CancelReservation"
        sent = recorded_request(mock)
        assert "OriginalTransactionKey" not in sent
        names = [p["Name"] for p in sent["Services"]["ServiceList"][0]["Parameters"]]
        assert "DataRequestKey" in names
        assert response.key == "KL-CAN-1"
        mock.assert_all_consumed()


class TestUpdateReservation:
    def test_posts_update_reservation_to_data_request(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KL-UPD-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaBuilder(client)

        response = builder.updateReservation(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "UpdateReservation"
        assert response.key == "KL-UPD-1"
        mock.assert_all_consumed()


class TestExtendReservation:
    def test_posts_extend_reservation_to_data_request(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KL-EXT-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaBuilder(client)

        response = builder.extendReservation(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "ExtendReservation"
        assert response.key == "KL-EXT-1"
        mock.assert_all_consumed()


def test_klarna_has_no_add_shipping_info_action():
    """AddShippingInfo is not a klarna action — the gateway rejects it, so the
    builder exposes no such method (shipping details ride on Pay)."""
    _, client = wire_recording_http()
    assert not hasattr(KlarnaBuilder(client), "addShippingInfo")
