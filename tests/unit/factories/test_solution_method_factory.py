import logging

import pytest

from buckaroo.factories.solution_method_factory import SolutionMethodFactory
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from buckaroo.builders.solutions.subscription_builder import SubscriptionBuilder
from buckaroo.builders.solutions.default_builder import DefaultBuilder


@pytest.fixture(autouse=True)
def _snapshot_registry():
    snapshot = SolutionMethodFactory._solution_methods.copy()
    try:
        yield snapshot
    finally:
        SolutionMethodFactory._solution_methods.clear()
        SolutionMethodFactory._solution_methods.update(snapshot)


@pytest.fixture
def client():
    return object()


@pytest.mark.parametrize(
    "method,builder_class",
    list(SolutionMethodFactory._solution_methods.items()),
)
def test_create_builder_returns_registered_class(method, builder_class, client):
    builder = SolutionMethodFactory.create_builder(method, client)
    assert isinstance(builder, builder_class)
    assert isinstance(builder, SolutionBuilder)


@pytest.mark.parametrize(
    "method",
    list(SolutionMethodFactory._solution_methods.keys()),
)
def test_is_method_supported_true_for_registered(method):
    assert SolutionMethodFactory.is_method_supported(method) is True


def test_get_available_methods_lists_all_registered_keys():
    assert set(SolutionMethodFactory.get_available_methods()) == set(
        SolutionMethodFactory._solution_methods.keys()
    )


def test_create_builder_is_case_insensitive(client):
    builder = SolutionMethodFactory.create_builder("SUBSCRIPTION", client)
    assert isinstance(builder, SubscriptionBuilder)


def test_create_builder_unknown_method_falls_back_to_default_with_warning(client, caplog):
    with caplog.at_level(logging.WARNING):
        builder = SolutionMethodFactory.create_builder("unknown", client)

    assert isinstance(builder, DefaultBuilder)
    assert any(
        "Unsupported payment method: unknown" in record.getMessage()
        and "DefaultBuilder" in record.getMessage()
        for record in caplog.records
    )


def test_is_method_supported_false_for_unknown():
    assert SolutionMethodFactory.is_method_supported("xxx") is False


class _CustomSolutionBuilder(SolutionBuilder):
    def get_service_name(self):
        return "Custom"

    def get_allowed_service_parameters(self, action="Pay"):
        return {}


def test_register_method_adds_new_entry(client):
    SolutionMethodFactory.register_method("custom", _CustomSolutionBuilder)
    assert SolutionMethodFactory.is_method_supported("custom") is True
    assert isinstance(
        SolutionMethodFactory.create_builder("custom", client), _CustomSolutionBuilder
    )


def test_register_method_lowercases_and_overrides(client):
    SolutionMethodFactory.register_method("SUBSCRIPTION", _CustomSolutionBuilder)
    assert isinstance(
        SolutionMethodFactory.create_builder("subscription", client),
        _CustomSolutionBuilder,
    )


def test_detect_method_from_payload_returns_method_lowercased():
    assert (
        SolutionMethodFactory.detect_method_from_payload({"method": "subscription"})
        == "subscription"
    )


def test_detect_method_from_payload_lowercases_uppercase_method():
    assert (
        SolutionMethodFactory.detect_method_from_payload({"method": "SUBSCRIPTION"})
        == "subscription"
    )


# SolutionMethodFactory.detect_method_from_payload deliberately does NOT warn
# on fallback — diverges from PaymentMethodFactory. Locked in here.
@pytest.mark.parametrize("payload", [{}, {"other": "thing"}], ids=["empty", "missing_method_key"])
def test_detect_method_from_payload_fallback_is_silent(payload, caplog):
    with caplog.at_level(logging.WARNING):
        result = SolutionMethodFactory.detect_method_from_payload(payload)
    assert result == "default"
    assert caplog.records == []
