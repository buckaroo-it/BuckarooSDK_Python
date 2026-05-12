"""Shared fixtures for feature tests."""

import pytest

from buckaroo.app import Buckaroo, BuckarooConfig
from tests.support.recording_mock import RecordingMock


@pytest.fixture
def buckaroo(mock_strategy):
    """Buckaroo app with MockBuckaroo injected as HTTP strategy."""
    app = Buckaroo(
        BuckarooConfig(
            store_key="test_store_key",
            secret_key="test_secret_key",
            mode="test",
            enable_logging=False,
        )
    )
    app.client.http_client.http_strategy = mock_strategy
    return app


@pytest.fixture
def recording_mock(request):
    """Fresh :class:`RecordingMock` per test, asserts-consumed on clean teardown.

    Use together with :func:`recording_buckaroo` when a feature test needs to
    assert on the exact JSON that reached the wire (Action, Parameters, etc.).
    """
    mock = RecordingMock()
    yield mock
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call is not None and rep_call.failed:
        return
    mock.assert_all_consumed()


@pytest.fixture
def recording_buckaroo(recording_mock):
    """Buckaroo app with :class:`RecordingMock` injected as HTTP strategy."""
    app = Buckaroo(
        BuckarooConfig(
            store_key="test_store_key",
            secret_key="test_secret_key",
            mode="test",
            enable_logging=False,
        )
    )
    app.client.http_client.http_strategy = recording_mock
    return app
