"""Shared fixtures for service-layer tests."""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from tests.support.mock_buckaroo import MockBuckaroo


@pytest.fixture
def client(mock_strategy: MockBuckaroo) -> BuckarooClient:
    """BuckarooClient wired to ``mock_strategy`` — no real HTTP."""
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock_strategy
    return c
