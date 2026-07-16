"""Parametrized contract tests over :data:`SolutionMethodFactory._solution_methods`.

Mirrors the payments concrete-builder contract suite. Every registered solution
builder must:

* instantiate with a :class:`BuckarooClient`,
* return a non-empty ``str`` from :meth:`get_service_name`,
* return a ``dict`` from :meth:`get_allowed_service_parameters` for the
  canonical action of the method.

The canonical action for each registered method is encoded in
``CANONICAL_ACTIONS`` below — `subscription` uses ``CreateSubscription``, which
matches :meth:`SubscriptionBuilder.createSubscription`.
"""

from __future__ import annotations

from typing import Dict, Type

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from buckaroo.factories.solution_method_factory import SolutionMethodFactory


# Canonical action per registered solution method. Keys must match
# ``SolutionMethodFactory._solution_methods``.
CANONICAL_ACTIONS: Dict[str, str] = {
    "subscription": "CreateSubscription",
    "emandate": "GetIssuerList",
    "emandateb2b": "GetIssuerList",
    "marketplaces": "Split",
}


@pytest.mark.parametrize(
    "method,builder_class",
    sorted(SolutionMethodFactory._solution_methods.items()),
)
def test_solution_builder_contract(
    method: str,
    builder_class: Type[SolutionBuilder],
    client: BuckarooClient,
) -> None:
    """Each registered builder instantiates and exposes the contract surface."""
    builder = builder_class(client)

    assert isinstance(builder, SolutionBuilder)

    name = builder.get_service_name()
    assert isinstance(name, str)
    assert name, f"{builder_class.__name__}.get_service_name() returned empty string"

    action = CANONICAL_ACTIONS[method]
    allowed = builder.get_allowed_service_parameters(action)
    assert isinstance(allowed, dict)


def test_canonical_actions_cover_every_registered_method() -> None:
    """Guard: keep ``CANONICAL_ACTIONS`` in sync with the registry."""
    assert set(CANONICAL_ACTIONS) == set(SolutionMethodFactory._solution_methods)
