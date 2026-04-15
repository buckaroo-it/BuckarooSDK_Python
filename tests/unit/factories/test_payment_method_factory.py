import logging

import pytest

from buckaroo.builders.payments.default_builder import DefaultBuilder
from buckaroo.builders.payments.ideal_builder import IdealBuilder
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.factories.payment_method_factory import PaymentMethodFactory


@pytest.fixture(autouse=True)
def _registry_snapshot():
    snapshot = dict(PaymentMethodFactory._payment_methods)
    try:
        yield snapshot
    finally:
        PaymentMethodFactory._payment_methods.clear()
        PaymentMethodFactory._payment_methods.update(snapshot)


@pytest.fixture
def client():
    return object()


# Unreachable camelCase keys (currently only "externalPayment") are excluded here
# and covered separately by a strict xfail below.
_REACHABLE_REGISTRY = {
    k: v for k, v in PaymentMethodFactory._payment_methods.items() if k == k.lower()
}

# Tripwire: if a future developer adds another camelCase key to the registry,
# this test fails and forces them to either lowercase it or explicitly widen
# the known-unreachable set (and add a matching xfail).
_KNOWN_UNREACHABLE_CAMELCASE_KEYS = {"externalPayment"}


def test_camelcase_registry_keys_are_locked_down():
    unreachable = {
        k for k in PaymentMethodFactory._payment_methods if k != k.lower()
    }
    assert unreachable == _KNOWN_UNREACHABLE_CAMELCASE_KEYS


@pytest.mark.parametrize("method, builder_class", list(_REACHABLE_REGISTRY.items()))
def test_create_builder_returns_registered_class_instance(method, builder_class, client):
    builder = PaymentMethodFactory.create_builder(method, client)
    assert isinstance(builder, builder_class)


@pytest.mark.parametrize("method, builder_class", list(_REACHABLE_REGISTRY.items()))
def test_create_builder_returns_payment_builder_subclass(method, builder_class, client):
    builder = PaymentMethodFactory.create_builder(method, client)
    assert isinstance(builder, PaymentBuilder)


@pytest.mark.parametrize("method", list(_REACHABLE_REGISTRY.keys()))
def test_is_method_supported_true_for_every_registered_method(method):
    assert PaymentMethodFactory.is_method_supported(method) is True


@pytest.mark.xfail(
    reason=(
        "Registry key 'externalPayment' is camelCase but create_builder() / "
        "is_method_supported() lowercase input before lookup, making the entry "
        "unreachable through the public API."
    ),
    strict=True,
)
def test_mixed_case_registry_key_is_reachable(client):
    from buckaroo.builders.payments.external_payment_builder import (
        ExternalPaymentBuilder,
    )

    assert PaymentMethodFactory.is_method_supported("externalPayment") is True
    builder = PaymentMethodFactory.create_builder("externalPayment", client)
    assert isinstance(builder, ExternalPaymentBuilder)


def test_get_available_methods_lists_every_registry_key():
    available = PaymentMethodFactory.get_available_methods()
    assert isinstance(available, list)
    assert set(available) == set(PaymentMethodFactory._payment_methods.keys())


def test_create_builder_is_case_insensitive(client):
    builder = PaymentMethodFactory.create_builder("IDEAL", client)
    assert isinstance(builder, IdealBuilder)


def test_create_builder_unknown_falls_back_to_default_and_warns(client, caplog):
    with caplog.at_level(logging.WARNING):
        builder = PaymentMethodFactory.create_builder("unknown", client)

    assert isinstance(builder, DefaultBuilder)
    assert any(
        "Unsupported payment method" in r.getMessage() and "unknown" in r.getMessage()
        for r in caplog.records
    )


def test_is_method_supported_false_for_unknown():
    assert PaymentMethodFactory.is_method_supported("XXX") is False


class _CustomBuilder(PaymentBuilder):
    def get_service_name(self):
        return "custom"

    def get_allowed_service_parameters(self, action="Pay"):
        return {}


def test_register_method_adds_new_entry(client):
    PaymentMethodFactory.register_method("custom", _CustomBuilder)
    assert PaymentMethodFactory.is_method_supported("custom") is True
    builder = PaymentMethodFactory.create_builder("custom", client)
    assert isinstance(builder, _CustomBuilder)


def test_register_method_overrides_existing_entry(client):
    PaymentMethodFactory.register_method("ideal", _CustomBuilder)
    builder = PaymentMethodFactory.create_builder("ideal", client)
    assert isinstance(builder, _CustomBuilder)


def test_register_method_lowercases_key(client):
    PaymentMethodFactory.register_method("MiXeD", _CustomBuilder)
    assert PaymentMethodFactory.is_method_supported("mixed") is True
    assert isinstance(
        PaymentMethodFactory.create_builder("MIXED", client), _CustomBuilder
    )


def test_detect_from_explicit_method_field():
    assert PaymentMethodFactory.detect_method_from_payload({"method": "ideal"}) == "ideal"


def test_detect_from_method_field_is_lowercased():
    assert PaymentMethodFactory.detect_method_from_payload({"method": "IDEAL"}) == "ideal"


def test_detect_from_service_list_single_registered():
    payload = {"Services": {"ServiceList": [{"Name": "creditcard"}]}}
    assert PaymentMethodFactory.detect_method_from_payload(payload) == "creditcard"


def test_detect_from_service_list_skips_unknown_and_picks_first_registered():
    payload = {
        "Services": {
            "ServiceList": [{"Name": "unknown"}, {"Name": "ideal"}],
        }
    }
    assert PaymentMethodFactory.detect_method_from_payload(payload) == "ideal"


def test_detect_method_field_beats_service_list():
    payload = {
        "method": "ideal",
        "Services": {"ServiceList": [{"Name": "creditcard"}]},
    }
    assert PaymentMethodFactory.detect_method_from_payload(payload) == "ideal"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"Services": {"ServiceList": []}},
        {"Services": {"ServiceList": [{"Name": "unknown"}]}},
    ],
    ids=["empty", "empty_service_list", "only_unknown_service"],
)
def test_detect_unresolvable_payload_returns_default_and_warns(payload, caplog):
    with caplog.at_level(logging.WARNING):
        result = PaymentMethodFactory.detect_method_from_payload(payload)
    assert result == "default"
    assert any(
        "Cannot determine payment method" in r.getMessage() for r in caplog.records
    )
