"""Shared contract tests for every concrete payment builder in the factory registry.

Lands first in phase 7. Parametrizes over
``PaymentMethodFactory._payment_methods`` so any registry entry that fails the
builder contract surfaces before per-builder work starts.

These are *surface* tests: instantiation, ``get_service_name()`` shape, and
``get_allowed_service_parameters("Pay")`` shape. Per-builder behaviour lives in
the dedicated test file for each builder.

The capability matrix asserts that the documented method names on each
capability mixin are present and callable on every subclass that mixes it in.
Actual behaviour of those methods is covered by the phase-4 capability tests
under ``tests/unit/builders/payments/capabilities/``.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Type

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
from buckaroo.builders.payments.payment_builder import PaymentBuilder
from buckaroo.factories.payment_method_factory import PaymentMethodFactory


REGISTRY: List[Tuple[str, Type[PaymentBuilder]]] = sorted(
    PaymentMethodFactory._payment_methods.items()
)


# Documented public methods each capability mixin contributes. Read off the
# mixin source — ``BankTransferCapabilities`` inherits from ``InstantRefundCapable``
# and ``FastCheckoutCapable`` so it exposes both of their methods.
CAPABILITY_METHODS: Dict[Type, List[str]] = {
    AuthorizeCaptureCapable: [
        "authorize",
        "authorizeEncrypted",
        "cancelAuthorize",
    ],
    BankTransferCapabilities: ["instantRefund", "payFastCheckout"],
    EncryptedPayCapable: ["payEncrypted"],
    InstantRefundCapable: ["instantRefund"],
    FastCheckoutCapable: ["payFastCheckout"],
}


def test_registry_has_sanity_floor():
    """Sanity floor so an accidental registry wipe fails loudly. The per-entry
    parametrized tests below catch per-builder damage."""
    assert len(REGISTRY) >= 20


@pytest.mark.parametrize(
    "method_name,builder_class", REGISTRY, ids=lambda x: x if isinstance(x, str) else x.__name__
)
def test_builder_instantiates_with_client(method_name, builder_class, client):
    builder = builder_class(client)
    assert isinstance(builder, PaymentBuilder)


@pytest.mark.parametrize(
    "method_name,builder_class", REGISTRY, ids=lambda x: x if isinstance(x, str) else x.__name__
)
def test_builder_get_service_name_returns_non_empty_string(method_name, builder_class, client):
    builder = builder_class(client)
    service_name = builder.get_service_name()
    assert isinstance(service_name, str)
    assert service_name != ""


@pytest.mark.parametrize(
    "method_name,builder_class", REGISTRY, ids=lambda x: x if isinstance(x, str) else x.__name__
)
def test_builder_get_allowed_service_parameters_pay_returns_dict(
    method_name, builder_class, client
):
    builder = builder_class(client)
    allowed = builder.get_allowed_service_parameters("Pay")
    assert isinstance(allowed, dict)


def _capability_matrix_params():
    """Yield (capability, method_name, builder_name, builder_class) for every
    registry entry that mixes in each capability."""
    rows = []
    for capability, methods in CAPABILITY_METHODS.items():
        for method_name, builder_class in REGISTRY:
            if not issubclass(builder_class, capability):
                continue
            for meth in methods:
                rows.append(
                    pytest.param(
                        capability,
                        meth,
                        method_name,
                        builder_class,
                        id=f"{capability.__name__}.{meth}-{method_name}",
                    )
                )
    return rows


@pytest.mark.parametrize("capability,method,method_name,builder_class", _capability_matrix_params())
def test_capability_method_present_and_callable(
    capability, method, method_name, builder_class, client
):
    builder = builder_class(client)
    assert hasattr(builder, method), (
        f"{builder_class.__name__} mixes in {capability.__name__} but is missing method {method!r}"
    )
    assert callable(getattr(builder, method))


# ---------------------------------------------------------------------------
# Capability-declaration matrix
#
# Pins the expected capability mixin set per registry entry. Historically the
# same assertion was duplicated in every per-builder file that shipped with
# no capabilities; the matrix below replaces those copies. Add the mixin to
# the builder's set here when a new capability lands.

KNOWN_MIXINS: List[Type] = list(CAPABILITY_METHODS.keys())

# BankTransferCapabilities extends both InstantRefundCapable and
# FastCheckoutCapable, so declaring BankTransferCapabilities implies the other
# two. The expected sets below include every mixin the builder is a subclass
# of — direct mixin plus transitive bases.
EXPECTED_CAPABILITIES: Dict[str, set] = {
    "creditcard": {EncryptedPayCapable, AuthorizeCaptureCapable},
    "riverty": {AuthorizeCaptureCapable},
    "ideal": {BankTransferCapabilities, InstantRefundCapable, FastCheckoutCapable},
    "paybybank": {BankTransferCapabilities, InstantRefundCapable, FastCheckoutCapable},
    "payconiq": {BankTransferCapabilities, InstantRefundCapable, FastCheckoutCapable},
    "sofort": {BankTransferCapabilities, InstantRefundCapable, FastCheckoutCapable},
}


@pytest.mark.parametrize(
    "method_name,builder_class", REGISTRY, ids=lambda x: x if isinstance(x, str) else x.__name__
)
@pytest.mark.parametrize("mixin", KNOWN_MIXINS, ids=lambda c: c.__name__)
def test_builder_declares_only_expected_capabilities(method_name, builder_class, mixin, client):
    expected = EXPECTED_CAPABILITIES.get(method_name, set())
    actual = issubclass(builder_class, mixin)
    assert actual is (mixin in expected), (
        f"{builder_class.__name__} capability mismatch for {mixin.__name__}: "
        f"issubclass={actual}, expected={mixin in expected}"
    )


# ---------------------------------------------------------------------------
# Inherited-base-method matrix
#
# Every concrete builder inherits these public action methods from
# :class:`BaseBuilder`. The per-builder copies of this assertion used to live
# inline; consolidating here keeps the contract in one place.

INHERITED_BASE_METHODS: List[str] = [
    "pay",
    "refund",
    "capture",
    "cancel",
    "partial_refund",
    "build",
    "execute_action",
]


@pytest.mark.parametrize(
    "method_name,builder_class", REGISTRY, ids=lambda x: x if isinstance(x, str) else x.__name__
)
@pytest.mark.parametrize("base_method", INHERITED_BASE_METHODS)
def test_inherited_base_builder_methods_callable(method_name, builder_class, base_method, client):
    builder = builder_class(client)
    assert hasattr(builder, base_method), (
        f"{builder_class.__name__} is missing inherited BaseBuilder method {base_method!r}"
    )
    assert callable(getattr(builder, base_method))
