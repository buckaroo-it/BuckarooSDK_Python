"""Behavior tests for :class:`buckaroo._buckaroo_client.BuckarooClient`.

Exercises the public surface:

- constructor credential validation (store/secret key must be non-empty)
- environment properties (``is_test_environment`` / ``is_live_environment``)
- ``api_endpoint`` delegation to the config
- ``confirm_credential`` round-trip against the injected HTTP strategy
- ``get_config_info`` exposes safe-to-log fields only

The HTTP layer is wired to :class:`tests.support.recording_mock.RecordingMock`
so ``confirm_credential`` round-trips without touching the network and we can
inspect the signed request.
"""

from __future__ import annotations

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.config.buckaroo_config import (
    BuckarooConfig,
    Environment,
)
from buckaroo.exceptions._authentication_error import AuthenticationError
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import RecordingMock


# ---------------------------------------------------------------------------
# Construction + credential validation


def test_constructs_with_valid_keys():
    client = BuckarooClient(store_key="X", secret_key="Y")
    assert client.store_key == "X"
    assert client.secret_key == "Y"


def test_strips_whitespace_from_keys():
    client = BuckarooClient(store_key="  X  ", secret_key="\tY\n")
    assert client.store_key == "X"
    assert client.secret_key == "Y"


@pytest.mark.parametrize(
    "store_key, secret_key",
    [
        ("", "secret"),
        ("   ", "secret"),
        (None, "secret"),
    ],
)
def test_missing_store_key_raises_authentication_error(store_key, secret_key):
    with pytest.raises(AuthenticationError):
        BuckarooClient(store_key=store_key, secret_key=secret_key)


@pytest.mark.parametrize(
    "store_key, secret_key",
    [
        ("store", ""),
        ("store", "   "),
        ("store", None),
    ],
)
def test_missing_secret_key_raises_authentication_error(store_key, secret_key):
    with pytest.raises(AuthenticationError):
        BuckarooClient(store_key=store_key, secret_key=secret_key)


def test_both_keys_empty_raises_authentication_error():
    with pytest.raises(AuthenticationError):
        BuckarooClient(store_key="", secret_key="")


def test_both_keys_none_raises_authentication_error():
    with pytest.raises(AuthenticationError):
        BuckarooClient(store_key=None, secret_key=None)


# ---------------------------------------------------------------------------
# Configuration wiring


def test_default_mode_is_test_environment():
    client = BuckarooClient("store", "secret")
    assert client.is_test_environment is True
    assert client.is_live_environment is False


def test_mode_live_sets_live_environment():
    client = BuckarooClient("store", "secret", mode="live")
    assert client.is_live_environment is True
    assert client.is_test_environment is False


def test_explicit_config_overrides_mode():
    config = BuckarooConfig(environment=Environment.LIVE)
    # mode says test, but the explicit config should win
    client = BuckarooClient("store", "secret", mode="test", config=config)
    assert client.is_live_environment is True
    assert client.is_test_environment is False
    assert client.config is config


def test_api_endpoint_delegates_to_config():
    config = BuckarooConfig(environment=Environment.TEST)
    client = BuckarooClient("store", "secret", config=config)
    assert client.api_endpoint == config.api_endpoint
    assert client.api_endpoint == "https://testcheckout.buckaroo.nl"


def test_api_endpoint_reflects_live_config():
    config = BuckarooConfig(environment=Environment.LIVE)
    client = BuckarooClient("store", "secret", config=config)
    assert client.api_endpoint == "https://checkout.buckaroo.nl"


def test_http_strategy_argument_is_accepted_and_stored():
    client = BuckarooClient("store", "secret", http_strategy="requests")
    assert client.http_strategy == "requests"


# ---------------------------------------------------------------------------
# confirm_credential


def test_confirm_credential_returns_true_on_success():
    client = BuckarooClient("store", "secret")
    mock = MockBuckaroo()
    mock.queue(
        BuckarooMockRequest.json(
            "GET",
            "*/json/Transaction/Specification/ideal",
            {"ok": True},
            status=200,
        )
    )
    client.http_client.http_strategy = mock

    assert client.confirm_credential() is True
    mock.assert_all_consumed()


def test_confirm_credential_hits_specification_ideal_endpoint():
    client = BuckarooClient("store", "secret")
    mock = RecordingMock()
    mock.queue(
        BuckarooMockRequest.json(
            "GET",
            "*/json/Transaction/Specification/ideal",
            {"ok": True},
            status=200,
        )
    )
    client.http_client.http_strategy = mock

    client.confirm_credential()

    assert len(mock.calls) == 1
    call = mock.calls[0]
    assert call["method"] == "GET"
    assert call["url"].endswith("/json/Transaction/Specification/ideal")
    # URL should be built on top of the configured (test) endpoint.
    assert call["url"].startswith("https://testcheckout.buckaroo.nl")


def test_confirm_credential_signs_request_with_hmac_authorization_header():
    client = BuckarooClient("store_key_xyz", "secret_key_abc")
    mock = RecordingMock()
    mock.queue(
        BuckarooMockRequest.json(
            "GET",
            "*/json/Transaction/Specification/ideal",
            {"ok": True},
            status=200,
        )
    )
    client.http_client.http_strategy = mock

    client.confirm_credential()

    headers = mock.calls[0]["headers"]
    assert "Authorization" in headers
    auth = headers["Authorization"]
    # Verify HMAC scheme and that the store key is present; strict
    # wire-format assertions live in tests/unit/http/test_client.py.
    assert auth.startswith("hmac ")
    assert "store_key_xyz" in auth


def test_confirm_credential_returns_false_on_authentication_error():
    # 401 / 403 — BuckarooHttpClient raises AuthenticationError,
    # confirm_credential must swallow it and return False.
    client = BuckarooClient("store", "secret")
    mock = MockBuckaroo()
    mock.queue(
        BuckarooMockRequest.json(
            "GET",
            "*/json/Transaction/Specification/ideal",
            {"error": "unauthorized"},
            status=401,
        )
    )
    client.http_client.http_strategy = mock

    assert client.confirm_credential() is False
    mock.assert_all_consumed()


def test_confirm_credential_returns_false_on_forbidden():
    client = BuckarooClient("store", "secret")
    mock = MockBuckaroo()
    mock.queue(
        BuckarooMockRequest.json(
            "GET",
            "*/json/Transaction/Specification/ideal",
            {"error": "forbidden"},
            status=403,
        )
    )
    client.http_client.http_strategy = mock

    assert client.confirm_credential() is False
    mock.assert_all_consumed()


def test_confirm_credential_returns_false_on_server_error():
    # 5xx — BuckarooHttpClient raises BuckarooApiError,
    # confirm_credential must catch it and return False.
    client = BuckarooClient("store", "secret")
    mock = MockBuckaroo()
    mock.queue(
        BuckarooMockRequest.json(
            "GET",
            "*/json/Transaction/Specification/ideal",
            {"error": "server"},
            status=500,
        )
    )
    client.http_client.http_strategy = mock

    assert client.confirm_credential() is False
    mock.assert_all_consumed()


def test_confirm_credential_returns_false_on_transport_exception():
    client = BuckarooClient("store", "secret")
    mock = MockBuckaroo()
    mock.queue(
        BuckarooMockRequest("GET", "*/json/Transaction/Specification/ideal")
        .with_exception(RuntimeError("network dead"))
    )
    client.http_client.http_strategy = mock

    assert client.confirm_credential() is False
    mock.assert_all_consumed()


# ---------------------------------------------------------------------------
# get_config_info


@pytest.mark.parametrize(
    "sensitive_field",
    [
        "secret_key",
        "secretKey",
        "store_key",
        "storeKey",
        "password",
        "api_key",
        "apiKey",
        "token",
        "Authorization",
    ],
)
def test_get_config_info_excludes_sensitive_fields(sensitive_field):
    client = BuckarooClient("store", "super-secret-value")
    info = client.get_config_info()
    assert sensitive_field not in info
    # Defensive: no value in the returned dict should leak the secret.
    assert "super-secret-value" not in repr(info)


def test_get_config_info_exposes_safe_config_fields():
    client = BuckarooClient("store", "secret", mode="test")
    info = client.get_config_info()

    assert info["environment"] == "test"
    assert info["api_endpoint"] == "https://testcheckout.buckaroo.nl"
    assert info["timeout"] == client.config.timeout
    assert info["retry_attempts"] == client.config.retry_attempts
    assert info["api_version"] == client.config.api_version.value
    assert info["logging_enabled"] == client.config.logging_enabled


def test_get_config_info_returns_dict():
    client = BuckarooClient("store", "secret")
    assert isinstance(client.get_config_info(), dict)
