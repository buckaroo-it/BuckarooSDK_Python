"""Factory for one-off :class:`PaymentBuilder` subclasses used in tests.

Keeps phase-4 tests for builder bases and capability mixins decoupled from any
concrete payment method. Callers pick the service name, allowed parameters
per action, and which capability mixins to compose in — no imports of
``IdealBuilder`` / ``CreditcardBuilder`` / etc. required.

Usage::

    from tests.support.builders import make_test_builder, populate_required_fields
    from buckaroo.builders.payments.capabilities.authorize_capture_capable import (
        AuthorizeCaptureCapable,
    )

    builder = make_test_builder(
        client,
        service_name="dummy",
        allowed_params={"Pay": {"issuer": {"type": str, "required": False}}},
        capabilities=(AuthorizeCaptureCapable,),
    )
    populate_required_fields(builder)
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Type

from buckaroo.builders.payments.payment_builder import PaymentBuilder


def make_test_builder(
    client: Any,
    *,
    service_name: str = "dummy",
    allowed_params: Optional[Dict[str, Any]] = None,
    capabilities: Iterable[Type] = (),
) -> PaymentBuilder:
    """Build a throwaway :class:`PaymentBuilder` subclass and return an instance.

    Args:
        client: The client instance the builder is bound to.
        service_name: Value for ``_serviceName`` and return value of
            ``get_service_name()``.
        allowed_params: Mapping of action name to allowed-parameter spec.
            The value for each action is returned verbatim from
            ``get_allowed_service_parameters(action)``. The validator expects
            a dict like ``{"issuer": {"type": str, "required": False}}``;
            lighter-weight callers may pass lists of names. Unknown actions
            return ``{}``.
        capabilities: Capability mixin classes to compose into the subclass
            (e.g. ``EncryptedPayCapable``, ``AuthorizeCaptureCapable``).
    """
    params_map: Dict[str, Any] = dict(allowed_params or {})
    bases: tuple = (PaymentBuilder, *tuple(capabilities))

    class _TestBuilder(*bases):
        _serviceName = service_name

        def get_service_name(self) -> str:
            return service_name

        def get_allowed_service_parameters(self, action: str = "Pay"):
            return params_map.get(action, {})

    _TestBuilder.__name__ = "TestBuilder"
    _TestBuilder.__qualname__ = "TestBuilder"

    return _TestBuilder(client)


def populate_required_fields(
    builder,
    *,
    currency: str = "EUR",
    amount: float = 10.0,
    description: str = "desc",
    invoice: str = "INV-1",
    return_url: str = "https://ret.example/ok",
    return_url_cancel: str = "https://ret.example/cancel",
    return_url_error: str = "https://ret.example/error",
    return_url_reject: str = "https://ret.example/reject",
):
    """Apply every required core setter so ``build()`` passes validation.

    Any field can be overridden via keyword argument. Returns the builder so
    the helper can be chained.
    """
    return (
        builder.currency(currency)
        .amount(amount)
        .description(description)
        .invoice(invoice)
        .return_url(return_url)
        .return_url_cancel(return_url_cancel)
        .return_url_error(return_url_error)
        .return_url_reject(return_url_reject)
    )


def strip_amount_debit_from_build(builder):
    """Wrap ``builder.build`` so the resulting ``to_dict()`` omits ``AmountDebit``.

    Used to exercise the ``if 'AmountDebit' in request_data`` False branch on
    refund paths. The underlying ``PaymentRequest`` serializer always writes
    the key, so post-hoc removal is the minimal way to reach that branch.
    """
    real_build = builder.build

    def _build(*args, **kwargs):
        req = real_build(*args, **kwargs)
        original_to_dict = req.to_dict

        def _to_dict():
            d = original_to_dict()
            d.pop("AmountDebit", None)
            return d

        req.to_dict = _to_dict
        return req

    builder.build = _build
    return builder
