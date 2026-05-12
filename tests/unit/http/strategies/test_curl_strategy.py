"""Unit tests for buckaroo.http.strategies.curl_strategy."""

import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from buckaroo.http.strategies.curl_strategy import CurlStrategy
from buckaroo.http.strategies.http_strategy import HttpResponse


def _completed(stdout="", stderr="", returncode=0):
    """Build a stand-in for subprocess.CompletedProcess."""
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


class TestDefaults:
    def test_init_sets_default_configuration(self):
        strategy = CurlStrategy()

        assert strategy._timeout == 30
        assert strategy._verify_ssl is True
        assert strategy._retry_attempts == 3
        assert strategy._default_headers == {}


class TestConfigure:
    def test_configure_stores_all_options(self):
        strategy = CurlStrategy()

        strategy.configure(
            timeout=60,
            verify_ssl=False,
            retry_attempts=5,
            default_headers={"X-Foo": "bar"},
        )

        assert strategy._timeout == 60
        assert strategy._verify_ssl is False
        assert strategy._retry_attempts == 5
        assert strategy._default_headers == {"X-Foo": "bar"}

    def test_configure_with_no_args_applies_defaults(self):
        strategy = CurlStrategy()
        strategy._timeout = 99
        strategy._verify_ssl = False
        strategy._retry_attempts = 7
        strategy._default_headers = {"stale": "yes"}

        strategy.configure()

        assert strategy._timeout == 30
        assert strategy._verify_ssl is True
        assert strategy._retry_attempts == 3
        assert strategy._default_headers == {}


class TestBuildCurlCommand:
    def test_includes_required_flags_and_method(self):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method="post", url="https://api.test/path")

        assert cmd[0] == "curl"
        assert "-X" in cmd
        assert cmd[cmd.index("-X") + 1] == "POST"
        assert "--location" in cmd
        assert "--silent" in cmd
        assert "--show-error" in cmd
        assert "--fail-with-body" in cmd
        assert "--include" in cmd
        assert "--max-time" in cmd
        assert cmd[cmd.index("--max-time") + 1] == "30"

    def test_custom_timeout_is_stringified(self):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method="GET", url="https://x", timeout=45)

        assert cmd[cmd.index("--max-time") + 1] == "45"

    def test_adds_insecure_when_verify_ssl_false(self):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method="GET", url="https://x", verify_ssl=False)

        assert "--insecure" in cmd

    def test_omits_insecure_when_verify_ssl_true(self):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method="GET", url="https://x", verify_ssl=True)

        assert "--insecure" not in cmd

    def test_merges_default_headers_with_per_call_headers(self):
        strategy = CurlStrategy()
        strategy.configure(default_headers={"X-Default": "d", "X-Shared": "default"})

        cmd = strategy._build_curl_command(
            method="GET",
            url="https://x",
            headers={"X-Call": "c", "X-Shared": "perCall"},
        )

        header_values = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "-H"]
        assert "X-Default: d" in header_values
        assert "X-Call: c" in header_values
        # per-call wins over default for overlapping key
        assert "X-Shared: perCall" in header_values
        assert "X-Shared: default" not in header_values

    def test_headers_omitted_when_neither_default_nor_per_call_provided(self):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method="GET", url="https://x")

        assert "-H" not in cmd

    @pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
    def test_data_attached_for_write_methods(self, method):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method=method, url="https://x", data='{"a":1}')

        assert "--data" in cmd
        assert cmd[cmd.index("--data") + 1] == '{"a":1}'

    @pytest.mark.parametrize("method", ["GET", "DELETE"])
    def test_data_omitted_for_read_methods(self, method):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method=method, url="https://x", data='{"a":1}')

        assert "--data" not in cmd

    def test_data_omitted_when_data_is_none_even_for_post(self):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method="POST", url="https://x", data=None)

        assert "--data" not in cmd

    def test_url_is_last_argument(self):
        strategy = CurlStrategy()
        strategy.configure(default_headers={"X-Default": "d"})

        cmd = strategy._build_curl_command(
            method="POST",
            url="https://api.test/path",
            headers={"X-Call": "c"},
            data="body",
            verify_ssl=False,
        )

        assert cmd[-1] == "https://api.test/path"

    def test_lowercase_method_is_uppercased(self):
        strategy = CurlStrategy()

        cmd = strategy._build_curl_command(method="get", url="https://x")

        assert cmd[cmd.index("-X") + 1] == "GET"


class TestParseCurlOutput:
    def test_splits_on_crlf_crlf_and_parses_status_and_headers(self):
        strategy = CurlStrategy()
        stdout = (
            'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nX-Req-Id: abc\r\n\r\n{"ok": true}'
        )

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=0))

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["X-Req-Id"] == "abc"
        assert response.text == '{"ok": true}'
        assert response.success is True

    def test_falls_back_to_lf_lf_separator(self):
        strategy = CurlStrategy()
        stdout = "HTTP/1.1 201 Created\nLocation: /new\n\nbody-here"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=0))

        assert response.status_code == 201
        assert response.headers.get("Location") == "/new"
        assert response.text == "body-here"
        assert response.success is True

    def test_no_separator_treats_all_output_as_body(self):
        strategy = CurlStrategy()

        response = strategy._parse_curl_output(_completed(stdout="just-a-body", returncode=0))

        assert response.status_code == 200
        assert response.headers == {}
        assert response.text == "just-a-body"
        assert response.success is True

    def test_no_separator_with_nonzero_returncode_uses_returncode_as_status(self):
        strategy = CurlStrategy()

        response = strategy._parse_curl_output(_completed(stdout="garbled", returncode=7))

        assert response.status_code == 7
        assert response.headers == {}
        assert response.text == "garbled"
        assert response.success is False

    def test_unparseable_status_line_uses_returncode(self):
        strategy = CurlStrategy()
        stdout = "HTTP/1.1 NOTANUMBER Weird\r\n\r\nbody"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=42))

        assert response.status_code == 42
        assert response.text == "body"
        assert response.success is False

    def test_unparseable_status_line_with_zero_returncode_falls_back_to_500(self):
        strategy = CurlStrategy()
        stdout = "HTTP/1.1 NOTANUMBER Weird\r\n\r\nbody"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=0))

        assert response.status_code == 500
        assert response.text == "body"
        assert response.success is False

    def test_status_line_without_second_token_falls_back_to_returncode(self):
        strategy = CurlStrategy()
        # "HTTP/" is present but split() yields only one element → IndexError path
        stdout = "HTTP/1.1\r\n\r\nbody"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=9))

        assert response.status_code == 9
        assert response.text == "body"

    def test_header_section_without_http_marker_leaves_status_zero(self):
        strategy = CurlStrategy()
        # No "HTTP/" on the status line → skip status parse, still parse K:V headers
        stdout = "Server: nginx\r\nContent-Type: text/plain\r\n\r\nbody-text"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=0))

        assert response.status_code == 0
        assert response.headers.get("Content-Type") == "text/plain"
        assert response.text == "body-text"
        assert response.success is False

    def test_header_lines_without_colon_are_skipped(self):
        strategy = CurlStrategy()
        stdout = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nNotAHeaderLine\r\n\r\nbody"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=0))

        assert response.headers == {"Content-Type": "text/plain"}
        assert response.text == "body"

    def test_empty_stdout_returns_response_with_returncode_as_status(self):
        strategy = CurlStrategy()

        response = strategy._parse_curl_output(_completed(stdout="", stderr="", returncode=0))

        assert isinstance(response, HttpResponse)
        assert response.status_code == 0
        assert response.headers == {}
        assert response.text == ""
        assert response.success is True

    def test_empty_stdout_with_nonzero_returncode_is_unsuccessful(self):
        strategy = CurlStrategy()

        response = strategy._parse_curl_output(_completed(stdout="", stderr="boom", returncode=2))

        assert response.status_code == 2
        assert response.text == ""
        assert response.success is False

    def test_nonzero_exit_with_empty_body_replaces_body_with_stderr(self):
        strategy = CurlStrategy()
        # whitespace-only body and a stderr message → body becomes stderr
        stdout = "HTTP/1.1 000 \r\n\r\n   "

        response = strategy._parse_curl_output(
            _completed(stdout=stdout, stderr="curl: (6) Could not resolve host", returncode=6)
        )

        assert response.text == "curl: (6) Could not resolve host"

    def test_nonzero_exit_with_empty_body_and_no_stderr_uses_fallback_message(self):
        strategy = CurlStrategy()
        stdout = "HTTP/1.1 000 \r\n\r\n"

        response = strategy._parse_curl_output(_completed(stdout=stdout, stderr="", returncode=6))

        assert response.text == "Curl failed with exit code 6"

    def test_success_flag_follows_2xx_status(self):
        strategy = CurlStrategy()
        stdout = "HTTP/1.1 299 Custom\r\n\r\nok"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=0))

        assert response.success is True

    def test_success_flag_false_for_300_range(self):
        strategy = CurlStrategy()
        stdout = "HTTP/1.1 301 Moved\r\nLocation: /x\r\n\r\n"

        response = strategy._parse_curl_output(_completed(stdout=stdout, returncode=0))

        assert response.success is False


class TestRequestHappyPath:
    def test_returns_parsed_response_on_first_success(self):
        strategy = CurlStrategy()
        completed = _completed(
            stdout="HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nhello",
            returncode=0,
        )

        with patch("subprocess.run", return_value=completed) as run_mock:
            response = strategy.request(
                method="POST",
                url="https://api.test/path",
                headers={"X-Trace": "1"},
                data="payload",
                timeout=10,
                verify_ssl=False,
            )

        assert response.status_code == 200
        assert response.text == "hello"
        assert response.success is True
        run_mock.assert_called_once()
        args, kwargs = run_mock.call_args
        cmd = args[0]
        assert cmd[0] == "curl"
        assert cmd[-1] == "https://api.test/path"
        assert "--insecure" in cmd
        assert "--data" in cmd
        assert kwargs["timeout"] == 10
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is False

    def test_uses_configured_timeout_when_call_omits_it(self):
        strategy = CurlStrategy()
        strategy.configure(timeout=25)
        completed = _completed(stdout="HTTP/1.1 200 OK\r\n\r\n", returncode=0)

        with patch("subprocess.run", return_value=completed) as run_mock:
            strategy.request(method="GET", url="https://x")

        _args, kwargs = run_mock.call_args
        assert kwargs["timeout"] == 25


class TestRequestRetryLoop:
    def test_timeout_expired_retries_up_to_retry_attempts_then_raises(self):
        strategy = CurlStrategy()
        strategy.configure(retry_attempts=3)

        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="curl", timeout=5),
        ) as run_mock:
            with pytest.raises(Exception) as excinfo:
                strategy.request(method="GET", url="https://x", timeout=5)

        assert run_mock.call_count == 3
        assert "Request timeout after 5 seconds" in str(excinfo.value)

    def test_subprocess_error_retries_and_raises_curl_command_failed(self):
        strategy = CurlStrategy()
        strategy.configure(retry_attempts=2)

        with patch(
            "subprocess.run",
            side_effect=subprocess.SubprocessError("spawn failed"),
        ) as run_mock:
            with pytest.raises(Exception) as excinfo:
                strategy.request(method="GET", url="https://x")

        assert run_mock.call_count == 2
        assert "Curl command failed: spawn failed" in str(excinfo.value)

    def test_generic_exception_retries_and_raises_request_failed(self):
        strategy = CurlStrategy()
        strategy.configure(retry_attempts=2)

        with patch("subprocess.run", side_effect=RuntimeError("weird thing")) as run_mock:
            with pytest.raises(Exception) as excinfo:
                strategy.request(method="GET", url="https://x")

        assert run_mock.call_count == 2
        assert "Request failed: weird thing" in str(excinfo.value)

    def test_recovers_if_later_attempt_succeeds(self):
        strategy = CurlStrategy()
        strategy.configure(retry_attempts=3)
        completed = _completed(stdout="HTTP/1.1 200 OK\r\n\r\nok", returncode=0)

        side_effects = [
            subprocess.TimeoutExpired(cmd="curl", timeout=5),
            completed,
        ]

        with patch("subprocess.run", side_effect=side_effects) as run_mock:
            response = strategy.request(method="GET", url="https://x", timeout=5)

        assert run_mock.call_count == 2
        assert response.status_code == 200
        assert response.text == "ok"

    def test_zero_retry_attempts_raises_fallback_exception(self):
        strategy = CurlStrategy()
        strategy.configure(retry_attempts=0)

        with patch("subprocess.run") as run_mock:
            with pytest.raises(Exception) as excinfo:
                strategy.request(method="GET", url="https://x")

        run_mock.assert_not_called()
        assert "Request failed after all retry attempts" in str(excinfo.value)


class TestIsAvailable:
    def test_returns_true_when_curl_on_path(self):
        strategy = CurlStrategy()

        with patch("shutil.which", return_value="/usr/bin/curl") as which_mock:
            assert strategy.is_available() is True

        which_mock.assert_called_once_with("curl")

    def test_returns_false_when_curl_missing(self):
        strategy = CurlStrategy()

        with patch("shutil.which", return_value=None) as which_mock:
            assert strategy.is_available() is False

        which_mock.assert_called_once_with("curl")


class TestGetName:
    def test_returns_curl(self):
        assert CurlStrategy().get_name() == "curl"
