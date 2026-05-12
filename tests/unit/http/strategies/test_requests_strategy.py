"""Unit tests for buckaroo.http.strategies.requests_strategy."""

import builtins
import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest

from buckaroo.http.strategies import requests_strategy as rs_module
from buckaroo.http.strategies.http_strategy import HttpResponse
from buckaroo.http.strategies.requests_strategy import RequestsStrategy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_response(status_code=200, text="ok", headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = headers or {"Content-Type": "application/json"}
    return resp


# ---------------------------------------------------------------------------
# get_name / is_available
# ---------------------------------------------------------------------------


class TestGetName:
    def test_returns_requests(self):
        assert RequestsStrategy().get_name() == "requests"


class TestIsAvailable:
    def test_reflects_flag_when_true(self, monkeypatch):
        monkeypatch.setattr(rs_module, "REQUESTS_AVAILABLE", True)
        assert RequestsStrategy().is_available() is True

    def test_reflects_flag_when_false(self, monkeypatch):
        monkeypatch.setattr(rs_module, "REQUESTS_AVAILABLE", False)
        assert RequestsStrategy().is_available() is False


# ---------------------------------------------------------------------------
# configure()
# ---------------------------------------------------------------------------


class TestConfigureDefaults:
    def test_creates_session_and_mounts_adapter_with_retry(self, monkeypatch):
        strategy = RequestsStrategy()

        mounted = {}
        session_instance = MagicMock()
        session_instance.headers = {}

        def mount(prefix, adapter):
            mounted[prefix] = adapter

        session_instance.mount.side_effect = mount

        session_cls = MagicMock(return_value=session_instance)
        adapter_cls = MagicMock(return_value=MagicMock(name="adapter"))
        retry_cls = MagicMock(return_value=MagicMock(name="retry"))

        monkeypatch.setattr(rs_module.requests, "Session", session_cls)
        monkeypatch.setattr(rs_module, "HTTPAdapter", adapter_cls)
        monkeypatch.setattr(rs_module, "Retry", retry_cls)

        strategy.configure()

        assert strategy.session is session_instance
        assert strategy._retry_attempts == 3
        assert strategy._retry_delay == 1.0

        retry_cls.assert_called_once_with(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET", "PUT", "DELETE"],
        )
        adapter_cls.assert_called_once_with(max_retries=retry_cls.return_value)
        assert session_instance.mount.call_count == 2
        assert "http://" in mounted and "https://" in mounted


class TestConfigureWithKwargs:
    def test_applies_custom_retry_and_default_headers(self, monkeypatch):
        strategy = RequestsStrategy()

        session_instance = MagicMock()
        session_instance.headers = MagicMock()

        session_cls = MagicMock(return_value=session_instance)
        adapter_cls = MagicMock(return_value=MagicMock())
        retry_cls = MagicMock(return_value=MagicMock())

        monkeypatch.setattr(rs_module.requests, "Session", session_cls)
        monkeypatch.setattr(rs_module, "HTTPAdapter", adapter_cls)
        monkeypatch.setattr(rs_module, "Retry", retry_cls)

        strategy.configure(
            retry_attempts=7,
            retry_delay=2.5,
            default_headers={"X-Test": "1"},
        )

        assert strategy._retry_attempts == 7
        assert strategy._retry_delay == 2.5
        retry_cls.assert_called_once_with(
            total=7,
            backoff_factor=2.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET", "PUT", "DELETE"],
        )
        session_instance.headers.update.assert_called_once_with({"X-Test": "1"})


class TestConfigureRetryFallback:
    def test_falls_back_to_plain_max_retries_when_retry_raises_typeerror(self, monkeypatch):
        strategy = RequestsStrategy()

        session_instance = MagicMock()
        session_instance.headers = {}
        session_cls = MagicMock(return_value=session_instance)

        adapter_cls = MagicMock(return_value=MagicMock())

        def retry_raises(*args, **kwargs):
            raise TypeError("bad kwargs for this urllib3 version")

        monkeypatch.setattr(rs_module.requests, "Session", session_cls)
        monkeypatch.setattr(rs_module, "HTTPAdapter", adapter_cls)
        monkeypatch.setattr(rs_module, "Retry", retry_raises)

        strategy.configure(retry_attempts=5)

        adapter_cls.assert_called_once_with(max_retries=5)
        assert session_instance.mount.call_count == 2


class TestConfigureWithoutRequests:
    def test_raises_import_error_with_install_hint(self, monkeypatch):
        monkeypatch.setattr(rs_module, "REQUESTS_AVAILABLE", False)
        strategy = RequestsStrategy()

        with pytest.raises(ImportError) as excinfo:
            strategy.configure()

        assert "requests" in str(excinfo.value)
        assert "pip install requests" in str(excinfo.value)


# ---------------------------------------------------------------------------
# request()
# ---------------------------------------------------------------------------


class TestRequestLazyConfigure:
    def test_calls_configure_when_session_is_none(self, monkeypatch):
        strategy = RequestsStrategy()

        session_instance = MagicMock()
        session_instance.request.return_value = _fake_response()

        def fake_configure(**kwargs):
            strategy.session = session_instance

        monkeypatch.setattr(strategy, "configure", fake_configure)

        result = strategy.request("GET", "https://example.com")

        assert strategy.session is session_instance
        assert isinstance(result, HttpResponse)
        assert result.success is True


class TestRequestTimeout:
    def test_defaults_timeout_to_30_when_none(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("GET", "https://example.com")

        kwargs = strategy.session.request.call_args.kwargs
        assert kwargs["timeout"] == 30

    def test_passes_explicit_timeout_through(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("GET", "https://example.com", timeout=12)

        kwargs = strategy.session.request.call_args.kwargs
        assert kwargs["timeout"] == 12


class TestRequestVerifySsl:
    def test_passes_verify_true_by_default(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("GET", "https://example.com")

        assert strategy.session.request.call_args.kwargs["verify"] is True

    def test_passes_verify_false_when_disabled(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("GET", "https://example.com", verify_ssl=False)

        assert strategy.session.request.call_args.kwargs["verify"] is False


class TestRequestHeadersAndBody:
    def test_forwards_headers(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("GET", "https://example.com", headers={"X-A": "1"})

        assert strategy.session.request.call_args.kwargs["headers"] == {"X-A": "1"}

    def test_defaults_headers_to_empty_dict_when_none(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("GET", "https://example.com")

        assert strategy.session.request.call_args.kwargs["headers"] == {}

    def test_includes_data_when_provided(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("POST", "https://example.com", data="payload")

        assert strategy.session.request.call_args.kwargs["data"] == "payload"

    def test_omits_data_key_when_not_provided(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response()

        strategy.request("GET", "https://example.com")

        assert "data" not in strategy.session.request.call_args.kwargs


class TestRequestStatusMapping:
    @pytest.mark.parametrize(
        "status_code,expected_success",
        [
            (200, True),
            (201, True),
            (299, True),
            (301, False),
            (400, False),
            (404, False),
            (500, False),
            (503, False),
        ],
    )
    def test_success_flag_is_2xx_only(self, status_code, expected_success):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.return_value = _fake_response(
            status_code=status_code,
            text="body",
            headers={"X-H": "v"},
        )

        response = strategy.request("GET", "https://example.com")

        assert response.status_code == status_code
        assert response.success is expected_success
        assert response.text == "body"
        assert response.headers == {"X-H": "v"}


class TestRequestExceptionMapping:
    def test_timeout_is_wrapped_with_seconds_message(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.side_effect = rs_module.requests.exceptions.Timeout("slow")

        with pytest.raises(Exception) as excinfo:
            strategy.request("GET", "https://example.com", timeout=7)

        assert str(excinfo.value) == "Request timeout after 7 seconds"

    def test_timeout_none_produces_clean_message(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.side_effect = rs_module.requests.exceptions.Timeout("slow")

        with pytest.raises(Exception) as excinfo:
            strategy.request("GET", "https://example.com", timeout=None)

        assert str(excinfo.value) == "Request timeout"

    def test_connection_error_is_wrapped_with_fixed_message(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.side_effect = rs_module.requests.exceptions.ConnectionError("down")

        with pytest.raises(Exception) as excinfo:
            strategy.request("GET", "https://example.com")

        assert str(excinfo.value) == ("Connection error - check your internet connection")

    def test_generic_request_exception_is_wrapped_with_prefix(self):
        strategy = RequestsStrategy()
        strategy.session = MagicMock()
        strategy.session.request.side_effect = rs_module.requests.exceptions.RequestException(
            "boom"
        )

        with pytest.raises(Exception) as excinfo:
            strategy.request("GET", "https://example.com")

        assert str(excinfo.value) == "Request failed: boom"


# ---------------------------------------------------------------------------
# Import-time branches
# ---------------------------------------------------------------------------


MODULE_PATH = "buckaroo.http.strategies.requests_strategy"


def _reload_with_blocked(block_names):
    """Reload the module with specific imports blocked, return the reloaded module."""
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in block_names or any(name.startswith(b + ".") for b in block_names):
            raise ImportError(f"blocked: {name}")
        # Also handle `from x import y` style where fromlist decides target
        return original_import(name, globals, locals, fromlist, level)

    saved = sys.modules.pop(MODULE_PATH, None)
    try:
        with patch.object(builtins, "__import__", side_effect=fake_import):
            module = importlib.import_module(MODULE_PATH)
        return module
    finally:
        if saved is not None:
            sys.modules[MODULE_PATH] = saved


class TestImportFallbacks:
    def test_falls_back_to_requests_packages_urllib3_when_urllib3_missing(self):
        module = _reload_with_blocked({"urllib3"})

        assert module.REQUESTS_AVAILABLE is True
        # Retry came from requests.packages.urllib3, which is the urllib3 Retry class
        from requests.packages.urllib3.util.retry import Retry as FallbackRetry

        assert module.Retry is FallbackRetry

    def test_sets_flag_false_and_defines_dummies_when_requests_missing(self):
        module = _reload_with_blocked({"requests"})

        assert module.REQUESTS_AVAILABLE is False
        # Dummy stand-ins should be defined as plain classes
        assert isinstance(module.HTTPAdapter, type)
        assert isinstance(module.Retry, type)
        assert module.HTTPAdapter() is not None
        assert module.Retry() is not None
