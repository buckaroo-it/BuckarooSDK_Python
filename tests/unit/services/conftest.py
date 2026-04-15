"""Shared fixtures for service-layer tests."""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from tests.support.mock_buckaroo import MockBuckaroo


@pytest.fixture
def client():
    """BuckarooClient wired to a MockBuckaroo strategy — never dispatched."""
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = MockBuckaroo()
    return c
