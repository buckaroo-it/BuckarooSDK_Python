"""Shared pytest configuration and fixtures for the Buckaroo SDK test suite."""

import pytest

from tests.support.mock_buckaroo import MockBuckaroo


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Stash per-phase report on the item so fixtures can skip asserts on failure."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def mock_strategy(request):
    """Fresh :class:`MockBuckaroo` per test, asserts-consumed on clean teardown."""
    mock = MockBuckaroo()
    yield mock
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call is not None and rep_call.failed:
        return
    mock.assert_all_consumed()
