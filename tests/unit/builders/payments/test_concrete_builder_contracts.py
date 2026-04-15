"""Smoke tests pinning abstract-stub contracts on concrete payment builders.

These are regression tests surfaced during phase-4 bulletproof audit. They pin
that every concrete builder overrides :meth:`BaseBuilder.get_allowed_service_parameters`
and that :meth:`BaseBuilder.required_fields` is a method (not a property) on
subclasses that override it.

Fuller per-builder tests belong in phase-7 (concrete builders).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from buckaroo.builders.payments.external_payment_builder import ExternalPaymentBuilder
from buckaroo.builders.payments.ideal_qr_builder import IdealQrBuilder


def test_external_payment_builder_returns_empty_allowed_params():
    builder = ExternalPaymentBuilder(MagicMock())
    assert builder.get_allowed_service_parameters() == {}
    assert builder.get_allowed_service_parameters("Refund") == {}


def test_ideal_qr_builder_required_fields_is_callable_not_property():
    builder = IdealQrBuilder(MagicMock())
    fields = builder.required_fields("Pay")
    assert isinstance(fields, dict)
    assert "currency" in fields
