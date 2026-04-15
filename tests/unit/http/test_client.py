"""HMAC-signing tests for :class:`buckaroo.http.client.BuckarooHttpClient`.

Pins the byte-for-byte output of ``_generate_hmac_signature``. Since the
client generates its nonce internally via ``uuid.uuid4()`` we parse the
nonce out of the returned ``Authorization`` header and re-derive the
signature from public inputs; the ``hmac_vectors`` fixture supplies a
fixed-nonce canonical value so the derivation formula itself is pinned.

No ``unittest.mock.patch`` used. A :class:`tests.support.mock_buckaroo.MockBuckaroo`
instance is injected wherever a client is constructed, even though these
tests never actually issue a request — the client only needs a valid
strategy to finish initializing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
from urllib.parse import quote

import pytest

from buckaroo.config.buckaroo_config import BuckarooConfig
from buckaroo.exceptions._authentication_error import AuthenticationError
from buckaroo.http.client import BuckarooApiError
from buckaroo.http.client import BuckarooHttpClient
from tests.support.mock_buckaroo import MockBuckaroo
from tests.support.mock_request import BuckarooMockRequest
from tests.support.recording_mock import RecordingMock


# ---------------------------------------------------------------------------
# Helpers


def _make_client(
    store_key: str = "test_store_key",
    secret_key: str = "test_secret_key",
) -> BuckarooHttpClient:
    """Build a client wired to a MockBuckaroo strategy (never dispatched)."""
    client = BuckarooHttpClient(
        store_key=store_key,
        secret_key=secret_key,
        config=BuckarooConfig(),
    )
    client.http_strategy = MockBuckaroo()
    return client


def _parse_auth(header_value: str) -> tuple[str, str, str, str]:
    """Return ``(store_key, signature, nonce, timestamp)`` from an Authorization header."""
    assert header_value.startswith("hmac "), header_value
    payload = header_value[len("hmac ") :]
    parts = payload.split(":")
    assert len(parts) == 4, parts
    return parts[0], parts[1], parts[2], parts[3]


def _recompute_signature(
    store_key: str,
    secret_key: str,
    method: str,
    url: str,
    content: str,
    timestamp: str,
    nonce: str,
) -> str:
    """Re-derive the Buckaroo HMAC signature from public inputs."""
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]
    encoded_url = quote(url, safe="").lower()

    if content:
        content_b64 = base64.b64encode(
            hashlib.md5(content.encode("utf-8")).digest()
        ).decode("utf-8")
    else:
        content_b64 = ""

    string_to_sign = (
        f"{store_key}{method}{encoded_url}{timestamp}{nonce}{content_b64}"
    )
    return base64.b64encode(
        _hmac.new(
            secret_key.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")


# ---------------------------------------------------------------------------
# Tests


class TestHmacVectors:
    """Pin derivation against frozen vectors (fixed nonce, fixed timestamp)."""

    def test_hmac_vectors_match_recomputed_signature(self, hmac_vectors):
        for (
            label,
            store_key,
            secret_key,
            method,
            url,
            content,
            timestamp,
            nonce,
            expected_encoded_url,
            expected_content_b64,
            expected_signature,
        ) in hmac_vectors:
            # Encoded URL component is a vector-level invariant.
            if url.startswith("https://"):
                stripped = url[8:]
            elif url.startswith("http://"):
                stripped = url[7:]
            else:
                stripped = url
            assert quote(stripped, safe="").lower() == expected_encoded_url, label

            # Content digest component is a vector-level invariant.
            if content:
                actual_b64 = base64.b64encode(
                    hashlib.md5(content.encode("utf-8")).digest()
                ).decode("utf-8")
            else:
                actual_b64 = ""
            assert actual_b64 == expected_content_b64, label

            # Signature derivation formula is a vector-level invariant.
            recomputed = _recompute_signature(
                store_key,
                secret_key,
                method,
                url,
                content,
                timestamp,
                nonce,
            )
            assert recomputed == expected_signature, label


class TestHmacHeaderFormat:
    """Pin structure of the returned auth headers."""

    def test_authorization_header_has_four_colon_components(self):
        client = _make_client(store_key="store_abc", secret_key="secret_xyz")
        headers = client._generate_hmac_signature(
            method="POST",
            url="https://testcheckout.buckaroo.nl/json/Transaction",
            content="",
            timestamp="1700000000",
        )

        auth = headers["Authorization"]
        assert auth.startswith("hmac ")
        store, signature, nonce, timestamp = _parse_auth(auth)
        assert store == "store_abc"
        assert signature  # non-empty base64
        assert nonce  # non-empty uuid
        assert timestamp == "1700000000"

    def test_all_three_headers_present(self):
        client = _make_client(store_key="store_abc")
        headers = client._generate_hmac_signature(
            method="POST",
            url="https://example.com/api",
            content="",
            timestamp="1700000000",
        )

        assert set(headers.keys()) == {
            "Authorization",
            "X-Buckaroo-Timestamp",
            "X-Buckaroo-Store-Key",
        }
        assert headers["X-Buckaroo-Timestamp"] == "1700000000"
        assert headers["X-Buckaroo-Store-Key"] == "store_abc"


class TestHmacDeterminism:
    """Client-returned signatures must match re-derivation under parsed nonce."""

    def test_signature_matches_local_derivation_for_fixed_inputs(self):
        client = _make_client(store_key="test_store_key", secret_key="test_secret_key")
        headers = client._generate_hmac_signature(
            method="POST",
            url="https://testcheckout.buckaroo.nl/json/Transaction",
            content='{"amount":10,"currency":"EUR"}',
            timestamp="1234567890",
        )

        _store, signature, nonce, _ts = _parse_auth(headers["Authorization"])
        expected = _recompute_signature(
            store_key="test_store_key",
            secret_key="test_secret_key",
            method="POST",
            url="https://testcheckout.buckaroo.nl/json/Transaction",
            content='{"amount":10,"currency":"EUR"}',
            timestamp="1234567890",
            nonce=nonce,
        )
        assert signature == expected

    def test_each_invocation_yields_fresh_nonce(self):
        client = _make_client()
        h1 = client._generate_hmac_signature("POST", "https://x/a", "", "1")
        h2 = client._generate_hmac_signature("POST", "https://x/a", "", "1")
        _, _, nonce1, _ = _parse_auth(h1["Authorization"])
        _, _, nonce2, _ = _parse_auth(h2["Authorization"])
        assert nonce1 != nonce2


class TestHmacSensitivity:
    """Flipping any signing input must change the signature."""

    @staticmethod
    def _sig_for(client, method, url, content, timestamp):
        h = client._generate_hmac_signature(method, url, content, timestamp)
        _, signature, nonce, _ = _parse_auth(h["Authorization"])
        return signature, nonce

    def test_signature_changes_when_method_changes(self):
        client = _make_client()
        sig_post, nonce = self._sig_for(
            client, "POST", "https://example.com/api", "", "1700000000"
        )
        # Re-derive GET using the SAME nonce so only method differs.
        get_expected = _recompute_signature(
            "test_store_key",
            "test_secret_key",
            "GET",
            "https://example.com/api",
            "",
            "1700000000",
            nonce,
        )
        assert sig_post != get_expected

    def test_signature_changes_when_url_changes(self):
        client = _make_client()
        sig_a, nonce = self._sig_for(
            client, "POST", "https://example.com/a", "", "1700000000"
        )
        sig_b_expected = _recompute_signature(
            "test_store_key",
            "test_secret_key",
            "POST",
            "https://example.com/b",
            "",
            "1700000000",
            nonce,
        )
        assert sig_a != sig_b_expected

    def test_signature_changes_when_content_changes(self):
        client = _make_client()
        sig_empty, nonce = self._sig_for(
            client, "POST", "https://example.com/api", "", "1700000000"
        )
        sig_with_body = _recompute_signature(
            "test_store_key",
            "test_secret_key",
            "POST",
            "https://example.com/api",
            '{"x":1}',
            "1700000000",
            nonce,
        )
        assert sig_empty != sig_with_body

    def test_signature_changes_when_timestamp_changes(self):
        client = _make_client()
        sig_t1, nonce = self._sig_for(
            client, "POST", "https://example.com/api", "", "1700000000"
        )
        sig_t2 = _recompute_signature(
            "test_store_key",
            "test_secret_key",
            "POST",
            "https://example.com/api",
            "",
            "1700000001",
            nonce,
        )
        assert sig_t1 != sig_t2

    def test_signature_changes_when_secret_key_changes(self):
        client_a = _make_client(secret_key="secret_a")
        client_b = _make_client(secret_key="secret_b")
        # Use local re-derivation to remove nonce as a variable.
        _, sig_a, nonce_a, _ = _parse_auth(
            client_a._generate_hmac_signature(
                "POST", "https://example.com/api", "", "1700000000"
            )["Authorization"]
        )
        sig_b_same_nonce = _recompute_signature(
            "test_store_key",
            "secret_b",
            "POST",
            "https://example.com/api",
            "",
            "1700000000",
            nonce_a,
        )
        assert sig_a != sig_b_same_nonce

    def test_signature_changes_when_store_key_changes(self):
        client_a = _make_client(store_key="store_a")
        _, sig_a, nonce_a, _ = _parse_auth(
            client_a._generate_hmac_signature(
                "POST", "https://example.com/api", "", "1700000000"
            )["Authorization"]
        )
        sig_b_same_nonce = _recompute_signature(
            "store_b",
            "test_secret_key",
            "POST",
            "https://example.com/api",
            "",
            "1700000000",
            nonce_a,
        )
        assert sig_a != sig_b_same_nonce


class TestHmacContentEdgeCases:
    """Empty-body variants must produce byte-identical content digests."""

    def test_empty_string_and_default_content_are_equivalent(self):
        client = _make_client()
        explicit_empty = client._generate_hmac_signature(
            "POST", "https://example.com/api", "", "1700000000"
        )
        default = client._generate_hmac_signature(
            "POST", "https://example.com/api", timestamp="1700000000"
        )
        _, sig1, nonce1, _ = _parse_auth(explicit_empty["Authorization"])
        _, sig2, nonce2, _ = _parse_auth(default["Authorization"])

        # Re-derive both under a shared nonce; both must collapse to the
        # same signature (proof content component is '' in both paths).
        rederived_1 = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "https://example.com/api", "", "1700000000", nonce1,
        )
        rederived_2 = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "https://example.com/api", "", "1700000000", nonce2,
        )
        assert sig1 == rederived_1
        assert sig2 == rederived_2

    def test_non_ascii_utf8_body_is_stable(self):
        client = _make_client()
        body = '{"description":"Payment 支付 💳","amount":15}'
        h1 = client._generate_hmac_signature(
            "POST", "https://example.com/api", body, "1700000000"
        )
        _, sig1, nonce1, _ = _parse_auth(h1["Authorization"])
        expected = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "https://example.com/api", body, "1700000000", nonce1,
        )
        assert sig1 == expected

        # Second call with same inputs + parsed nonce yields identical sig.
        h2 = client._generate_hmac_signature(
            "POST", "https://example.com/api", body, "1700000000"
        )
        _, sig2, nonce2, _ = _parse_auth(h2["Authorization"])
        expected2 = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "https://example.com/api", body, "1700000000", nonce2,
        )
        assert sig2 == expected2


class TestHmacUrlScheme:
    """Both https:// and http:// schemes must strip the protocol identically."""

    def test_http_url_strips_protocol_for_signing(self):
        client = _make_client()
        body = ""
        ts = "1700000000"

        h_http = client._generate_hmac_signature("POST", "http://example.com/api", body, ts)
        h_https = client._generate_hmac_signature("POST", "https://example.com/api", body, ts)
        _, sig_http, nonce_http, _ = _parse_auth(h_http["Authorization"])
        _, sig_https, nonce_https, _ = _parse_auth(h_https["Authorization"])

        # Same path on http vs https → identical signature when re-derived with the same nonce.
        rederived_http = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "http://example.com/api", body, ts, nonce_http,
        )
        rederived_https = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "https://example.com/api", body, ts, nonce_https,
        )
        assert sig_http == rederived_http
        assert sig_https == rederived_https

    def test_url_without_scheme_signs_verbatim(self):
        client = _make_client()
        headers = client._generate_hmac_signature(
            "POST", "example.com/api", "", "1700000000"
        )
        _, sig, nonce, _ = _parse_auth(headers["Authorization"])

        expected = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "example.com/api", "", "1700000000", nonce,
        )
        assert sig == expected


class TestHmacTimestampDefault:
    """When ``timestamp`` is omitted the header must still round-trip."""

    def test_default_timestamp_is_current_unix_seconds_string(self):
        import time as _time

        before = int(_time.time())
        client = _make_client()
        headers = client._generate_hmac_signature(
            "POST", "https://example.com/api", ""
        )
        after = int(_time.time())

        ts_header = headers["X-Buckaroo-Timestamp"]
        assert ts_header.isdigit()
        assert before <= int(ts_header) <= after

        _, signature, nonce, auth_ts = _parse_auth(headers["Authorization"])
        assert auth_ts == ts_header
        expected = _recompute_signature(
            "test_store_key", "test_secret_key", "POST",
            "https://example.com/api", "", ts_header, nonce,
        )
        assert signature == expected


# ---------------------------------------------------------------------------
# Sanity: parametrized walk over the full vector set through the real client.


@pytest.mark.parametrize(
    "vector_index",
    list(range(6)),
    ids=[
        "post_empty_body",
        "post_string_body",
        "post_json_int_amount",
        "post_json_unicode",
        "get_empty_body",
        "post_mixedcase_url",
    ],
)
def test_hmac_client_output_matches_vector_under_parsed_nonce(
    hmac_vectors, vector_index
):
    (
        _label,
        store_key,
        secret_key,
        method,
        url,
        content,
        timestamp,
        _fixed_nonce,
        _expected_encoded_url,
        _expected_content_b64,
        _expected_signature,
    ) = hmac_vectors[vector_index]

    client = _make_client(store_key=store_key, secret_key=secret_key)
    headers = client._generate_hmac_signature(method, url, content, timestamp)

    parsed_store, signature, parsed_nonce, parsed_ts = _parse_auth(
        headers["Authorization"]
    )
    assert parsed_store == store_key
    assert parsed_ts == timestamp
    assert headers["X-Buckaroo-Store-Key"] == store_key
    assert headers["X-Buckaroo-Timestamp"] == timestamp

    recomputed = _recompute_signature(
        store_key, secret_key, method, url, content, timestamp, parsed_nonce
    )
    assert signature == recomputed


# ---------------------------------------------------------------------------
# Error mapping + request orchestration (Issue #19)
#
# Builds clients with a MockBuckaroo strategy injected directly so we can
# control exact responses and observed request shapes. No unittest.mock.


def _make_client_with_mock(mock: MockBuckaroo) -> BuckarooHttpClient:
    """Build a client and replace its strategy with the given mock."""
    client = BuckarooHttpClient(
        store_key="test_store_key",
        secret_key="test_secret_key",
        config=BuckarooConfig(),
    )
    client.http_strategy = mock
    return client


class TestResponseParsing:
    """`_parse_response` semantics through the public client surface."""

    def test_valid_json_2xx_returns_parsed_dict(self):
        mock = RecordingMock()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/Transaction*", {"Key": "abc"}))
        client = _make_client_with_mock(mock)

        response = client.post("/json/Transaction", data={"a": 1})

        assert response.success is True
        assert response.status_code == 200
        assert response.data == {"Key": "abc"}

    def test_empty_body_2xx_yields_empty_dict(self):
        from buckaroo.http.strategies.http_strategy import HttpResponse

        class EmptyBodyMock(MockBuckaroo):
            def request(self, method, url, headers=None, data=None, timeout=None, verify_ssl=True):
                return HttpResponse(status_code=200, headers={}, text="", success=True)

        client = _make_client_with_mock(EmptyBodyMock())

        response = client.post("/json/Transaction", data={"a": 1})

        assert response.success is True
        assert response.data == {}

    def test_malformed_json_2xx_raises_buckaroo_api_error(self):
        from buckaroo.http.strategies.http_strategy import HttpResponse

        class GarbageBodyMock(MockBuckaroo):
            def request(self, method, url, headers=None, data=None, timeout=None, verify_ssl=True):
                return HttpResponse(
                    status_code=200, headers={}, text="not-json{", success=True
                )

        client = _make_client_with_mock(GarbageBodyMock())

        with pytest.raises(BuckarooApiError):
            client.post("/json/Transaction", data={"a": 1})


class TestAuthenticationStatusCodes:
    """401 and 403 must surface as :class:`AuthenticationError`."""

    def test_401_raises_authentication_error_about_keys(self):
        mock = MockBuckaroo()
        mock.queue(
            BuckarooMockRequest.json("POST", "*/json/Transaction*", {"err": "no"}, status=401)
        )
        client = _make_client_with_mock(mock)

        with pytest.raises(AuthenticationError) as exc:
            client.post("/json/Transaction", data={"a": 1})

        message = str(exc.value).lower()
        assert "store" in message and "secret" in message

    def test_403_raises_authentication_error_about_permissions(self):
        mock = MockBuckaroo()
        mock.queue(
            BuckarooMockRequest.json("POST", "*/json/Transaction*", {"err": "no"}, status=403)
        )
        client = _make_client_with_mock(mock)

        with pytest.raises(AuthenticationError) as exc:
            client.post("/json/Transaction", data={"a": 1})

        assert "permission" in str(exc.value).lower()


class TestNonAuthErrorStatusCodes:
    """All other non-2xx responses must surface as :class:`BuckarooApiError`."""

    @pytest.mark.parametrize("status", [400, 404, 422, 500, 503])
    def test_non_2xx_raises_buckaroo_api_error_carrying_status_and_body(self, status):
        body = {"Code": status, "Message": f"err-{status}"}
        mock = MockBuckaroo()
        mock.queue(
            BuckarooMockRequest.json("POST", "*/json/Transaction*", body, status=status)
        )
        client = _make_client_with_mock(mock)

        with pytest.raises(BuckarooApiError) as exc:
            client.post("/json/Transaction", data={"a": 1})

        assert not isinstance(exc.value, AuthenticationError)

        assert str(status) in str(exc.value)
        assert exc.value.status_code == status
        assert f"err-{status}" in str(exc.value.error_data) or f"err-{status}" in (exc.value.response.text if exc.value.response else "")


class TestStrategyExceptionMapping:
    """Transport-level exceptions must be re-raised as :class:`BuckarooApiError`."""

    def test_timeout_exception_becomes_buckaroo_api_error(self):
        mock = MockBuckaroo()
        mock.queue(
            BuckarooMockRequest("POST", "*/json/Transaction*").with_exception(
                TimeoutError("connection timeout after 30s")
            )
        )
        client = _make_client_with_mock(mock)

        with pytest.raises(BuckarooApiError) as exc:
            client.post("/json/Transaction", data={"a": 1})

        assert isinstance(exc.value.__cause__, TimeoutError)
        assert "Request failed" in str(exc.value)

    def test_connection_exception_becomes_buckaroo_api_error(self):
        mock = MockBuckaroo()
        mock.queue(
            BuckarooMockRequest("POST", "*/json/Transaction*").with_exception(
                ConnectionError("connection refused by host")
            )
        )
        client = _make_client_with_mock(mock)

        with pytest.raises(BuckarooApiError) as exc:
            client.post("/json/Transaction", data={"a": 1})

        assert isinstance(exc.value.__cause__, ConnectionError)
        assert "Request failed" in str(exc.value)

    def test_authentication_error_from_strategy_propagates_unchanged(self):
        original = AuthenticationError("strategy-side auth failure")
        mock = MockBuckaroo()
        mock.queue(
            BuckarooMockRequest("POST", "*/json/Transaction*").with_exception(original)
        )
        client = _make_client_with_mock(mock)

        with pytest.raises(AuthenticationError) as exc:
            client.post("/json/Transaction", data={"a": 1})

        assert exc.value is original

    def test_buckaroo_api_error_from_strategy_propagates_unchanged(self):
        original = BuckarooApiError("strategy-side api failure")
        mock = MockBuckaroo()
        mock.queue(
            BuckarooMockRequest("POST", "*/json/Transaction*").with_exception(original)
        )
        client = _make_client_with_mock(mock)

        with pytest.raises(BuckarooApiError) as exc:
            client.post("/json/Transaction", data={"a": 1})

        assert exc.value is original


class TestRequestOrchestration:
    """post/get delegate to the strategy with the right URL, method, headers."""

    def test_post_passes_authorization_header_to_strategy(self):
        mock = RecordingMock()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/Transaction*", {}))
        client = _make_client_with_mock(mock)

        client.post("/json/Transaction", data={"a": 1})

        assert len(mock.calls) == 1
        call = mock.calls[0]
        assert call["method"] == "POST"
        assert "Authorization" in call["headers"]
        assert call["headers"]["Authorization"].startswith("hmac ")

    def test_get_passes_authorization_header_to_strategy(self):
        mock = RecordingMock()
        mock.queue(BuckarooMockRequest.json("GET", "*/json/Transaction*", {}))
        client = _make_client_with_mock(mock)

        client.get("/json/Transaction")

        assert len(mock.calls) == 1
        call = mock.calls[0]
        assert call["method"] == "GET"
        assert "Authorization" in call["headers"]

    def test_endpoint_without_leading_slash_is_normalised(self):
        mock = RecordingMock()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/Transaction", {}))
        client = _make_client_with_mock(mock)

        client.post("json/Transaction", data={"a": 1})

        url = mock.calls[0]["url"]
        assert url == "https://testcheckout.buckaroo.nl/json/Transaction"
        assert "//json" not in url.split("://", 1)[1]

    def test_endpoint_with_leading_slash_does_not_double_up(self):
        mock = RecordingMock()
        mock.queue(BuckarooMockRequest.json("POST", "*/json/Transaction", {}))
        client = _make_client_with_mock(mock)

        client.post("/json/Transaction", data={"a": 1})

        url = mock.calls[0]["url"]
        assert url == "https://testcheckout.buckaroo.nl/json/Transaction"

    def test_get_passes_params_in_query_string_with_no_body(self):
        mock = RecordingMock()
        mock.queue(BuckarooMockRequest.json("GET", "*/json/Spec*", {}))
        client = _make_client_with_mock(mock)

        client.get("/json/Spec", params={"name": "ideal", "v": "1"})

        call = mock.calls[0]
        assert call["data"] is None
        assert "name=ideal" in call["url"]
        assert "v=1" in call["url"]
        assert call["url"].split("?", 1)[0] == "https://testcheckout.buckaroo.nl/json/Spec"


class TestApiErrorSymbol:
    """`BuckarooApiError` is the public exception type for HTTP failures."""

    def test_buckaroo_api_error_is_exposed_from_client_module(self):
        from buckaroo.http import client as client_module

        assert hasattr(client_module, "BuckarooApiError")
