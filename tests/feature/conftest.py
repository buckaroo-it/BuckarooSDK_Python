"""Shared fixtures for feature tests."""

import pytest

from buckaroo.app import Buckaroo, BuckarooConfig
from tests.support.mock_buckaroo import MockBuckaroo


@pytest.fixture
def mock_strategy():
    """Fresh MockBuckaroo strategy for each test."""
    return MockBuckaroo()


@pytest.fixture
def buckaroo(mock_strategy):
    """Buckaroo app with MockBuckaroo injected as HTTP strategy."""
    app = Buckaroo(BuckarooConfig(
        store_key="test_store_key",
        secret_key="test_secret_key",
        mode="test",
        enable_logging=False,
    ))
    app.client.http_client.http_strategy = mock_strategy
    return app


@pytest.fixture(autouse=True)
def _assert_mocks_consumed(mock_strategy):
    """Assert all queued mocks were consumed after each test."""
    yield
    mock_strategy.assert_all_consumed()
