"""Unit tests for :class:`SubscriptionBuilder`."""

from __future__ import annotations

import pytest

from buckaroo.builders.solutions.subscription_builder import SubscriptionBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from tests.support.mock_request import BuckarooMockRequest
from tests.support.builders import populate_required_fields


def test_construction_with_client_succeeds(client):
    builder = SubscriptionBuilder(client)
    assert isinstance(builder, SubscriptionBuilder)
    assert isinstance(builder, SolutionBuilder)


def test_get_service_name_returns_subscription(client):
    assert SubscriptionBuilder(client).get_service_name() == "Subscription"


def test_get_allowed_service_parameters_pay_snapshot(client):
    builder = SubscriptionBuilder(client)
    assert builder.get_allowed_service_parameters("Pay") == {}


def test_get_allowed_service_parameters_pay_is_case_insensitive(client):
    builder = SubscriptionBuilder(client)
    assert builder.get_allowed_service_parameters("pay") == (
        builder.get_allowed_service_parameters("Pay")
    )


def test_get_allowed_service_parameters_create_subscription_returns_empty(client):
    builder = SubscriptionBuilder(client)
    assert builder.get_allowed_service_parameters("CreateSubscription") == {}


@pytest.mark.parametrize("action", ["Refund", "Capture", "Authorize", "UnknownAction"])
def test_get_allowed_service_parameters_non_pay_returns_empty(client, action):
    assert SubscriptionBuilder(client).get_allowed_service_parameters(action) == {}


def test_create_subscription_posts_and_parses_response(client, mock_strategy):
    mock_strategy.queue(
        BuckarooMockRequest.json(
            "POST",
            "*/json/DataRequest*",
            {"Key": "sub-key-456", "Status": {"Code": {"Code": 190}}},
        )
    )

    response = (
        populate_required_fields(SubscriptionBuilder(client), amount=9.99)
        .createSubscription()
    )

    assert response.key == "sub-key-456"
    mock_strategy.assert_all_consumed()
