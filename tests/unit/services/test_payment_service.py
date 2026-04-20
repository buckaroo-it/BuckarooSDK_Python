"""Tests for :class:`buckaroo.services.payment_service.PaymentService`.

Verifies the service surface — builder selection, payload population via
``from_dict``, auto-detection from payload, and delegation to the
:class:`PaymentMethodFactory` — through the public API. The
``BuckarooClient`` is wired with a ``MockBuckaroo`` strategy (never
dispatched) so no network calls are required.
"""

from __future__ import annotations

import logging

import pytest

from buckaroo.builders.payments.credit_card_builder import CreditcardBuilder
from buckaroo.builders.payments.default_builder import DefaultBuilder
from buckaroo.builders.payments.ideal_builder import IdealBuilder
from buckaroo.services.payment_service import PaymentService


@pytest.fixture
def service(client):
    return PaymentService(client)


class TestCreatePayment:
    """``create_payment(method, params?)`` — builder selection + from_dict."""

    def test_returns_builder_registered_for_method(self, service):
        builder = service.create_payment("ideal")
        assert isinstance(builder, IdealBuilder)

    def test_is_case_insensitive(self, service):
        builder = service.create_payment("IDEAL")
        assert isinstance(builder, IdealBuilder)

    def test_populates_builder_from_params_via_from_dict(self, service):
        params = {
            "currency": "EUR",
            "amount": 12.5,
            "description": "test",
            "invoice": "INV-9",
            "return_url": "https://ex/ok",
            "return_url_cancel": "https://ex/cancel",
            "return_url_error": "https://ex/error",
            "return_url_reject": "https://ex/reject",
        }
        builder = service.create_payment("ideal", params)

        req = builder.build("Pay", validate=False)
        assert req.currency == "EUR"
        assert req.amount_debit == 12.5
        assert req.description == "test"
        assert req.invoice == "INV-9"
        assert req.return_url == "https://ex/ok"

    @pytest.mark.parametrize(
        "params,method,expected_cls",
        [
            (None, "creditcard", CreditcardBuilder),
            ({}, "ideal", IdealBuilder),
        ],
    )
    def test_falsy_params_skip_from_dict(self, service, params, method, expected_cls):
        builder = service.create_payment(method, params)
        assert isinstance(builder, expected_cls)
        # Falsy params must not populate required fields; build() surfaces that.
        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build("Pay", validate=False)

    def test_unknown_method_returns_default_builder_and_logs_warning(
        self, service, caplog
    ):
        with caplog.at_level(logging.WARNING):
            builder = service.create_payment("nope")
        assert isinstance(builder, DefaultBuilder)
        assert any("Unsupported payment method" in r.message for r in caplog.records)


class TestCreateAutoDetect:
    """``create(payload)`` — method auto-detection routing."""

    def test_detects_from_explicit_method_key(self, service):
        payload = {
            "method": "ideal",
            "amount": 5.0,
            "currency": "EUR",
            "description": "autodetect",
            "invoice": "INV-AD",
            "return_url": "https://ex/ok",
            "return_url_cancel": "https://ex/cancel",
            "return_url_error": "https://ex/error",
            "return_url_reject": "https://ex/reject",
        }
        builder = service.create(payload)
        assert isinstance(builder, IdealBuilder)
        req = builder.build("Pay", validate=False).to_dict()
        assert req["AmountDebit"] == 5.0
        assert req["Currency"] == "EUR"

    def test_detects_from_services_service_list(self, service):
        payload = {
            "Services": {"ServiceList": [{"Name": "creditcard"}]},
            "amount": 7.0,
            "currency": "EUR",
            "description": "autodetect",
            "invoice": "INV-AD",
            "return_url": "https://ex/ok",
            "return_url_cancel": "https://ex/cancel",
            "return_url_error": "https://ex/error",
            "return_url_reject": "https://ex/reject",
        }
        builder = service.create(payload)
        assert isinstance(builder, CreditcardBuilder)
        req = builder.build("Pay", validate=False).to_dict()
        assert req["AmountDebit"] == 7.0

    def test_empty_payload_falls_back_to_default_and_warns(self, service, caplog):
        with caplog.at_level(logging.WARNING):
            builder = service.create({})
        assert isinstance(builder, DefaultBuilder)
        assert any(
            "Cannot determine payment method" in r.message for r in caplog.records
        )


class TestFactoryDelegation:
    """``get_available_methods`` / ``is_method_supported`` delegate to factory."""

    def test_get_available_methods_includes_registered_methods(self, service):
        methods = service.get_available_methods()
        assert "ideal" in methods
        assert "creditcard" in methods
        assert "default" in methods

    def test_is_method_supported_true_for_registered(self, service):
        assert service.is_method_supported("ideal") is True

    def test_is_method_supported_is_case_insensitive(self, service):
        assert service.is_method_supported("IDEAL") is True

    def test_is_method_supported_false_for_unknown(self, service):
        assert service.is_method_supported("nope") is False
