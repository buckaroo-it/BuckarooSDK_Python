"""Shared fixtures for unit tests."""

import pytest


_BUCKAROO_ENV_VARS = (
    "BUCKAROO_STORE_KEY",
    "BUCKAROO_SECRET_KEY",
    "BUCKAROO_MODE",
    "BUCKAROO_LOG_LEVEL",
    "BUCKAROO_LOG_DESTINATION",
    "BUCKAROO_LOG_FILE",
    "BUCKAROO_LOG_MASK_SENSITIVE",
    "BUCKAROO_TIMEOUT",
    "BUCKAROO_RETRY_ATTEMPTS",
)


@pytest.fixture(autouse=True)
def _clean_buckaroo_env(monkeypatch):
    """Start every test with a clean BUCKAROO_* environment."""
    for name in _BUCKAROO_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def env_credentials(monkeypatch):
    """Set default BUCKAROO_STORE_KEY / BUCKAROO_SECRET_KEY and return monkeypatch for chaining."""
    monkeypatch.setenv("BUCKAROO_STORE_KEY", "sk")
    monkeypatch.setenv("BUCKAROO_SECRET_KEY", "ss")
    return monkeypatch
