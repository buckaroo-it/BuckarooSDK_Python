"""Unit tests for :class:`DefaultBuilder` (solutions).

Targets 100% line + branch coverage of
``buckaroo/builders/solutions/default_builder.py``. The solutions
``DefaultBuilder`` is a catch-all that unknown solution-method lookups fall
back to via :class:`SolutionMethodFactory`. It has no ``_serviceName``
class attribute, no capability mixins, and no solution-specific action
methods. The surface under test is:

- construction via ``BuckarooClient`` wired to :class:`MockBuckaroo`
- ``get_service_name()`` reading ``method`` from the payload (and falling
  back to ``"Unknown"`` when absent)
- ``get_allowed_service_parameters(action)`` returning ``{}`` for every
  action - the catch-all has no required params
- end-to-end build + execute through the mock strategy
"""

from __future__ import annotations

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.solutions.default_builder import DefaultBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from tests.support.mock_request import BuckarooMockRequest


def test_construction_with_client_succeeds(client: BuckarooClient) -> None:
    builder = DefaultBuilder(client)
    assert isinstance(builder, DefaultBuilder)
    assert isinstance(builder, SolutionBuilder)


def test_get_service_name_defaults_to_unknown(client: BuckarooClient) -> None:
    assert DefaultBuilder(client).get_service_name() == "Unknown"


def test_get_service_name_reads_method_from_payload(client: BuckarooClient) -> None:
    builder = DefaultBuilder(client).from_dict({"method": "CustomSolution"})
    assert builder.get_service_name() == "CustomSolution"


def test_get_allowed_service_parameters_returns_empty(client: BuckarooClient) -> None:
    assert DefaultBuilder(client).get_allowed_service_parameters("Pay") == {}
    assert DefaultBuilder(client).get_allowed_service_parameters("Refund") == {}
