"""Unit tests for :class:`SubscriptionBuilder`."""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.builders.solutions.subscription_builder import SubscriptionBuilder
from buckaroo.builders.solutions.solution_builder import SolutionBuilder
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest


@pytest.fixture
def mock_strategy():
    return MockBuckaroo()


@pytest.fixture
def client(mock_strategy):
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock_strategy
    return c


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
        SubscriptionBuilder(client)
        .currency("EUR")
        .amount(9.99)
        .description("Subscription order")
        .invoice("SUB-1")
        .return_url("https://example.test/return")
        .return_url_cancel("https://example.test/cancel")
        .return_url_error("https://example.test/error")
        .return_url_reject("https://example.test/reject")
        .createSubscription()
    )

    assert response.key == "sub-key-456"
    mock_strategy.assert_all_consumed()
