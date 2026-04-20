"""Shared fixtures for feature tests."""

import pytest

from buckaroo.app import Buckaroo, BuckarooConfig


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
