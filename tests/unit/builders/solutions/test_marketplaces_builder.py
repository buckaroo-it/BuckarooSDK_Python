"""Unit tests for :class:`MarketplacesBuilder`."""

from __future__ import annotations

import pytest

from buckaroo.builders.solutions.marketplaces_builder import MarketplacesBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from buckaroo.factories.solution_method_factory import SolutionMethodFactory
from buckaroo.models.payment_request import CombinableService


@pytest.fixture
def client():
    return object()


def test_is_a_solution_builder(client):
    assert isinstance(MarketplacesBuilder(client), SolutionBuilder)


def test_service_name_is_marketplaces(client):
    assert MarketplacesBuilder(client).get_service_name() == "Marketplaces"


def test_split_action_allows_grouped_and_days_parameters(client):
    allowed = MarketplacesBuilder(client).get_allowed_service_parameters("Split")
    assert set(allowed) == {"DaysUntilTransfer", "Marketplace", "Seller"}


def test_transfer_action_allows_only_split_groups(client):
    allowed = MarketplacesBuilder(client).get_allowed_service_parameters("Transfer")
    assert set(allowed) == {"Marketplace", "Seller"}


def test_refund_supplementary_action_allows_only_split_groups(client):
    allowed = MarketplacesBuilder(client).get_allowed_service_parameters("RefundSupplementary")
    assert set(allowed) == {"Marketplace", "Seller"}


def test_manual_transfer_action_allows_account_and_description_params(client):
    allowed = MarketplacesBuilder(client).get_allowed_service_parameters("ManualTransfer")
    assert set(allowed) == {
        "FromAccountId",
        "ToAccountId",
        "FromDescription",
        "ToDescription",
    }


def test_unknown_action_allows_no_parameters(client):
    assert MarketplacesBuilder(client).get_allowed_service_parameters("Bogus") == {}


def test_split_returns_combinable_service(client):
    mp = MarketplacesBuilder(client).split(
        {"marketplace": {"Amount": "10.00"}, "sellers": [{"AccountId": "S1", "Amount": "85.00"}]}
    )
    assert isinstance(mp, CombinableService)
    assert [s.name for s in mp.services] == ["Marketplaces"]
    assert mp.services[0].action == "Split"


def test_registered_under_marketplaces_key():
    assert SolutionMethodFactory._solution_methods["marketplaces"] is MarketplacesBuilder
