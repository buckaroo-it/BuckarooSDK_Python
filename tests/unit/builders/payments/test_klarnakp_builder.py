"""Per-builder unit tests for :class:`KlarnaKPBuilder`.

Phase 7.21 — KlarnaKP has reservation-based actions on top of ``Pay``:
``Reserve``, ``CancelReservation``, ``UpdateReservation``,
``ExtendReservation``, and ``AddShippingInfo``. Each has a builder-specific
method (``reserve``, ``cancelReservation``, ``updateReservation``,
``extendReservation``, ``addShippingInfo``) that posts to ``/json/DataRequest``
rather than ``/json/transaction``.

The source also narrows :meth:`required_fields` so only ``Reserve`` has any
required fields (currency + invoice); every other action returns ``{}``,
including ``Pay``. That is load-bearing behaviour — several of the builder-
specific action methods would otherwise fail ``_validate_required_fields``.

``KlarnaKPBuilder`` mixes in no capability classes; the docstring mentions
"bank transfer capabilities" but that is documentation drift, not inheritance.
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
from buckaroo.builders.payments.klarnakp_builder import KlarnaKPBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from tests.support.builders import populate_required_fields
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import recorded_action, recorded_request, wire_recording_http


# ---------------------------------------------------------------------------
# Fixtures


# ---------------------------------------------------------------------------
# Construction


def test_construct_with_client_returns_payment_builder(client):
    builder = KlarnaKPBuilder(client)
    assert isinstance(builder, KlarnaKPBuilder)
    assert isinstance(builder, PaymentBuilder)


# ---------------------------------------------------------------------------
# get_service_name


def test_get_service_name_returns_klarnakp(client):
    assert KlarnaKPBuilder(client).get_service_name() == "klarnakp"


# ---------------------------------------------------------------------------
# get_allowed_service_parameters — snapshot every KlarnaKP action


class TestGetAllowedServiceParameters:
    def test_pay_returns_reservation_number_spec(self, client):
        assert KlarnaKPBuilder(client).get_allowed_service_parameters("Pay") == {
            "reservationNumber": {
                "type": str,
                "required": True,
                "description": "Klarna KP reservation number",
            },
        }

    def test_cancel_reservation_returns_reservation_number_spec(self, client):
        assert KlarnaKPBuilder(client).get_allowed_service_parameters(
            "CancelReservation"
        ) == {
            "reservationNumber": {
                "type": str,
                "required": True,
                "description": "Klarna KP reservation number",
            },
        }

    def test_reserve_returns_operating_country_and_article_spec(self, client):
        assert KlarnaKPBuilder(client).get_allowed_service_parameters("Reserve") == {
            "operatingCountry": {
                "type": str,
                "required": True,
                "description": "Operating country code",
            },
            "article": {
                "type": list,
                "required": True,
                "description": "Klarna KP articles",
            },
        }

    def test_extend_reservation_returns_reservation_number_spec(self, client):
        assert KlarnaKPBuilder(client).get_allowed_service_parameters(
            "ExtendReservation"
        ) == {
            "reservationNumber": {
                "type": str,
                "required": True,
                "description": "Klarna KP reservation number",
            },
        }

    def test_extend_reservation_matches_pay_result(self, client):
        builder = KlarnaKPBuilder(client)
        assert builder.get_allowed_service_parameters("ExtendReservation") == builder.get_allowed_service_parameters("Pay")

    def test_update_reservation_returns_reservation_number_and_article_spec(self, client):
        assert KlarnaKPBuilder(client).get_allowed_service_parameters(
            "UpdateReservation"
        ) == {
            "reservationNumber": {
                "type": str,
                "required": True,
                "description": "Klarna KP reservation number",
            },
            "article": {
                "type": list,
                "required": True,
                "description": "Klarna KP articles",
            },
        }

    def test_add_shipping_info_returns_shipping_spec(self, client):
        assert KlarnaKPBuilder(client).get_allowed_service_parameters(
            "AddShippingInfo"
        ) == {
            "originalTransactionKey": {
                "type": str,
                "required": True,
                "description": "Original transaction key",
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

    def test_defaults_to_pay_when_action_omitted(self, client):
        builder = KlarnaKPBuilder(client)
        assert builder.get_allowed_service_parameters() == builder.get_allowed_service_parameters("Pay")

    def test_unknown_action_returns_empty_dict(self, client):
        assert KlarnaKPBuilder(client).get_allowed_service_parameters("Refund") == {}

    def test_action_matching_is_case_insensitive(self, client):
        """Source lowercases ``action`` before every branch comparison."""
        builder = KlarnaKPBuilder(client)
        assert builder.get_allowed_service_parameters("reserve") == builder.get_allowed_service_parameters("Reserve")
        assert builder.get_allowed_service_parameters("PAY") == builder.get_allowed_service_parameters("Pay")


# ---------------------------------------------------------------------------
# required_fields override


class TestRequiredFields:
    def test_reserve_requires_only_currency_and_invoice(self, client):
        builder = KlarnaKPBuilder(client).currency("EUR").invoice("INV-1")
        assert builder.required_fields("Reserve") == {
            "currency": "EUR",
            "invoice": "INV-1",
        }

    def test_reserve_case_insensitive_matches_Reserve_branch(self, client):
        builder = KlarnaKPBuilder(client).currency("EUR").invoice("INV-1")
        assert builder.required_fields("reserve") == builder.required_fields("Reserve")

    def test_non_reserve_action_returns_empty_dict(self, client):
        """Every action other than Reserve returns ``{}`` — overrides the base
        class which would otherwise require currency/amount/description/etc."""
        builder = KlarnaKPBuilder(client)
        assert builder.required_fields("Pay") == {}
        assert builder.required_fields("CancelReservation") == {}
        assert builder.required_fields("UpdateReservation") == {}
        assert builder.required_fields("ExtendReservation") == {}
        assert builder.required_fields("AddShippingInfo") == {}

    def test_defaults_to_pay_and_returns_empty_dict(self, client):
        assert KlarnaKPBuilder(client).required_fields() == {}


# ---------------------------------------------------------------------------
# Capability-mixin sanity — KlarnaKPBuilder mixes in nothing


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
def test_klarnakp_builder_does_not_inherit_capability_mixin(capability):
    assert not issubclass(KlarnaKPBuilder, capability), (
        f"KlarnaKPBuilder unexpectedly inherits {capability.__name__}; "
        "KlarnaKP does not mix in any capability classes per the SDK spec."
    )


# ---------------------------------------------------------------------------
# Base methods from PaymentBuilder are still present


class TestBaseBuilderSurfaceRemainsIntact:
    def test_pay_present_and_callable(self, client):
        builder = KlarnaKPBuilder(client)
        assert hasattr(builder, "pay")
        assert callable(builder.pay)

    def test_refund_present_and_callable(self, client):
        builder = KlarnaKPBuilder(client)
        assert hasattr(builder, "refund")
        assert callable(builder.refund)


# ---------------------------------------------------------------------------
# Builder-specific reservation action methods — end-to-end through MockBuckaroo


class TestReserve:
    def test_posts_reserve_to_data_request_endpoint_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KLKP-RES-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaKPBuilder(client).currency("EUR").invoice("INV-1")

        response = builder.reserve(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "Reserve"
        sent = recorded_request(mock)
        assert sent["Services"]["ServiceList"][0]["Name"] == "klarnakp"
        assert response.key == "KLKP-RES-1"
        mock.assert_all_consumed()


class TestCancelReservation:
    def test_posts_cancel_reservation_to_data_request_endpoint_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KLKP-CAN-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaKPBuilder(client)

        response = builder.cancelReservation(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "CancelReservation"
        assert response.key == "KLKP-CAN-1"
        mock.assert_all_consumed()


class TestUpdateReservation:
    def test_posts_update_reservation_to_data_request_endpoint_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KLKP-UPD-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaKPBuilder(client)

        response = builder.updateReservation(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "UpdateReservation"
        assert response.key == "KLKP-UPD-1"
        mock.assert_all_consumed()


class TestExtendReservation:
    def test_posts_extend_reservation_to_data_request_endpoint_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KLKP-EXT-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaKPBuilder(client)

        response = builder.extendReservation(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "ExtendReservation"
        assert response.key == "KLKP-EXT-1"
        mock.assert_all_consumed()


class TestAddShippingInfo:
    def test_posts_add_shipping_info_to_data_request_endpoint_and_parses_response(self):
        mock, client = wire_recording_http()
        mock.queue(
            BuckarooMockRequest.json(
                "POST",
                "*/json/DataRequest*",
                {"Key": "KLKP-SHP-1", "Status": {"Code": {"Code": 190}}},
            )
        )
        builder = KlarnaKPBuilder(client)

        response = builder.addShippingInfo(validate=False)

        assert "/json/DataRequest" in mock.calls[0]["url"]
        assert recorded_action(mock) == "AddShippingInfo"
        assert response.key == "KLKP-SHP-1"
        mock.assert_all_consumed()


# ---------------------------------------------------------------------------
# pay() still works — sanity that the base Pay path is not regressed


def test_pay_dispatches_klarnakp_service_to_transaction_endpoint():
    mock, client = wire_recording_http()
    mock.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/transaction*",
            {"Key": "KLKP-PAY-1", "Status": {"Code": {"Code": 190}}},
        )
    )
    # required_fields("Pay") returns {} so no setters are needed — but we set
    # them anyway so refactors that tighten required_fields don't break this.
    builder = populate_required_fields(KlarnaKPBuilder(client), amount=42.00)

    response = builder.pay(validate=False)

    assert "/json/transaction" in mock.calls[0]["url"].lower()
    sent = recorded_request(mock)
    service = sent["Services"]["ServiceList"][0]
    assert service["Name"] == "klarnakp"
    assert service["Action"] == "Pay"
    assert response.key == "KLKP-PAY-1"
    mock.assert_all_consumed()
