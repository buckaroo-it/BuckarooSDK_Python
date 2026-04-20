"""Tests for :class:`buckaroo.services.solution_service.SolutionService`.

Mirrors ``test_payment_service.py``: the ``BuckarooClient`` is wired with a
``MockBuckaroo`` strategy (never dispatched) so the service can be exercised
without any network. Asserts builder type and payload population through the
public interface only.
"""

from __future__ import annotations

import logging

import pytest

from buckaroo.builders.solutions.default_builder import DefaultBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from buckaroo.builders.solutions.subscription_builder import SubscriptionBuilder
from buckaroo.factories.solution_method_factory import SolutionMethodFactory
from buckaroo.services.solution_service import SolutionService


@pytest.fixture
def service(client):
    return SolutionService(client)


class TestCreateSolution:
    """``create_solution(method, params?)`` — builder selection + from_dict."""

    def test_returns_builder_registered_for_method(self, service):
        builder = service.create_solution("subscription")
        assert isinstance(builder, SubscriptionBuilder)

    def test_is_case_insensitive(self, service):
        builder = service.create_solution("SUBSCRIPTION")
        assert isinstance(builder, SubscriptionBuilder)

    def test_populates_builder_from_params_via_from_dict(self, service):
        params = {
            "currency": "EUR",
            "amount": 12.5,
            "description": "start sub",
            "invoice": "INV-9",
            "return_url": "https://ex/ok",
            "return_url_cancel": "https://ex/cancel",
            "return_url_error": "https://ex/error",
            "return_url_reject": "https://ex/reject",
        }
        builder = service.create_solution("subscription", params)

        assert isinstance(builder, SubscriptionBuilder)
        req = builder.build("Pay", validate=False)
        assert req.currency == "EUR"
        assert req.amount_debit == 12.5
        assert req.description == "start sub"
        assert req.invoice == "INV-9"
        assert req.return_url == "https://ex/ok"

    @pytest.mark.parametrize("params", [None, {}])
    def test_falsy_params_skip_from_dict(self, service, params):
        builder = service.create_solution("subscription", params)
        assert isinstance(builder, SubscriptionBuilder)
        # Falsy params must not populate any fields; request dict shows it.
        req = builder.build("Pay", validate=False).to_dict()
        assert req["Currency"] is None
        assert req["AmountDebit"] is None

    def test_unknown_method_returns_default_builder_and_logs_warning(
        self, service, caplog
    ):
        with caplog.at_level(logging.WARNING):
            builder = service.create_solution("nope")
        assert isinstance(builder, DefaultBuilder)
        assert any("Unsupported payment method" in r.message for r in caplog.records)

    def test_unknown_method_with_params_still_populates_default_builder(
        self, service
    ):
        params = {
            "currency": "USD",
            "amount": 7.0,
            "description": "fallback",
            "invoice": "INV-FB",
            "return_url": "https://ex/ok",
            "return_url_cancel": "https://ex/cancel",
            "return_url_error": "https://ex/error",
            "return_url_reject": "https://ex/reject",
        }
        builder = service.create_solution("unknown-thing", params)
        assert isinstance(builder, DefaultBuilder)
        req = builder.build("Pay", validate=False)
        assert req.currency == "USD"
        assert req.amount_debit == 7.0


class TestCreateAutoDetect:
    """``create(payload)`` — method auto-detection routing for solutions."""

    def test_detects_from_explicit_method_key(self, service):
        payload = {
            "method": "subscription",
            "currency": "EUR",
            "amount": 3.5,
            "description": "autodetect sub",
            "invoice": "INV-SUB",
            "return_url": "https://ex/ok",
            "return_url_cancel": "https://ex/cancel",
            "return_url_error": "https://ex/error",
            "return_url_reject": "https://ex/reject",
        }
        builder = service.create(payload)
        assert isinstance(builder, SubscriptionBuilder)
        req = builder.build("Pay", validate=False).to_dict()
        assert req["Currency"] == "EUR"
        assert req["AmountDebit"] == 3.5

    def test_method_key_is_case_insensitive(self, service):
        builder = service.create({"method": "SUBSCRIPTION"})
        assert isinstance(builder, SubscriptionBuilder)

    def test_empty_payload_falls_back_to_default_builder(self, service, caplog):
        with caplog.at_level(logging.WARNING):
            builder = service.create({})
        assert isinstance(builder, DefaultBuilder)
        assert any("Unsupported payment method" in r.message for r in caplog.records)

    def test_payload_without_method_key_uses_default_builder(self, service):
        payload = {
            "currency": "EUR",
            "amount": 1.0,
            "description": "no method",
            "invoice": "INV-NM",
            "return_url": "https://ex/ok",
            "return_url_cancel": "https://ex/cancel",
            "return_url_error": "https://ex/error",
            "return_url_reject": "https://ex/reject",
        }
        builder = service.create(payload)
        assert isinstance(builder, DefaultBuilder)
        req = builder.build("Pay", validate=False).to_dict()
        assert req["Currency"] == "EUR"
        assert req["AmountDebit"] == 1.0


class TestFactoryDelegation:
    """``get_available_methods`` / ``is_method_supported`` delegate to factory."""

    def test_get_available_methods_matches_factory(self, service):
        assert service.get_available_methods() == (
            SolutionMethodFactory.get_available_methods()
        )

    def test_get_available_methods_includes_subscription(self, service):
        assert "subscription" in service.get_available_methods()

    def test_is_method_supported_true_for_registered(self, service):
        assert service.is_method_supported("subscription") is True

    def test_is_method_supported_is_case_insensitive(self, service):
        assert service.is_method_supported("SUBSCRIPTION") is True

    def test_is_method_supported_false_for_unknown(self, service):
        assert service.is_method_supported("nope") is False


class TestSolutionBuilderInheritance:
    """Every dispatch path yields a ``SolutionBuilder`` subclass."""

    @pytest.mark.parametrize(
        "dispatch",
        [
            lambda s: s.create_solution("subscription"),
            lambda s: s.create_solution("unknown"),
            lambda s: s.create({"method": "subscription"}),
            lambda s: s.create({}),
        ],
        ids=["known", "unknown", "autodetect-known", "autodetect-empty"],
    )
    def test_returns_solution_builder(self, service, dispatch):
        assert isinstance(dispatch(service), SolutionBuilder)
