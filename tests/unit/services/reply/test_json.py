"""Tests for :class:`buckaroo.services.reply.json_reply.Json`.

Validates the inverse of :meth:`BuckarooHttpClient._generate_hmac_signature`
— given a known-good ``Authorization`` header, :class:`Json` must accept it.
"""

from __future__ import annotations

import pytest

from buckaroo.config.buckaroo_config import BuckarooConfig
from buckaroo.http.client import BuckarooHttpClient
from buckaroo.services.reply.json_reply import Json


STORE = "storekey123"
SECRET = "secretkey"


def _build_valid_header(method: str, url: str, body: str = "") -> str:
    """Generate a real Authorization header using the SDK's HMAC generator."""
    client = BuckarooHttpClient(STORE, SECRET, BuckarooConfig())
    return client._generate_hmac_signature(method, url, body)["Authorization"]


class TestValidate:
    def test_accepts_valid_header_for_empty_body(self):
        url = "https://checkout.buckaroo.nl/json/Transaction/Push"
        header = _build_valid_header("POST", url, "")
        assert Json(STORE, SECRET).validate(header, url, "POST", "") is True

    def test_accepts_valid_header_for_json_body(self):
        url = "https://checkout.buckaroo.nl/json/Transaction/Push"
        body = '{"Transaction":{"Status":{"Code":190}}}'
        header = _build_valid_header("POST", url, body)
        assert Json(STORE, SECRET).validate(header, url, "POST", body) is True

    def test_accepts_body_as_bytes(self):
        url = "https://checkout.buckaroo.nl/json/Transaction/Push"
        body = '{"k":"v"}'
        header = _build_valid_header("POST", url, body)
        assert Json(STORE, SECRET).validate(header, url, "POST", body.encode("utf-8")) is True

    def test_rejects_tampered_body(self):
        url = "https://checkout.buckaroo.nl/json/Transaction/Push"
        body = '{"Transaction":{"Status":{"Code":190}}}'
        header = _build_valid_header("POST", url, body)
        tampered = '{"Transaction":{"Status":{"Code":690}}}'
        assert Json(STORE, SECRET).validate(header, url, "POST", tampered) is False

    def test_rejects_tampered_uri(self):
        url = "https://checkout.buckaroo.nl/json/Transaction/Push"
        header = _build_valid_header("POST", url, "")
        assert (
            Json(STORE, SECRET).validate(
                header, "https://checkout.buckaroo.nl/json/Other", "POST", ""
            )
            is False
        )

    def test_rejects_tampered_method(self):
        url = "https://checkout.buckaroo.nl/json/Transaction/Push"
        header = _build_valid_header("POST", url, "")
        assert Json(STORE, SECRET).validate(header, url, "GET", "") is False

    def test_rejects_wrong_secret_key(self):
        url = "https://checkout.buckaroo.nl/json/Transaction/Push"
        header = _build_valid_header("POST", url, "")
        assert Json(STORE, "different_secret").validate(header, url, "POST", "") is False

    def test_rejects_malformed_header_too_few_parts(self):
        assert Json(STORE, SECRET).validate("hmac storekey:hash:nonce", "/x", "POST", "") is False

    def test_rejects_malformed_header_too_many_parts(self):
        assert (
            Json(STORE, SECRET).validate(
                "hmac storekey:hash:nonce:time:extra", "/x", "POST", ""
            )
            is False
        )

    def test_rejects_empty_header(self):
        assert Json(STORE, SECRET).validate("", "/x", "POST", "") is False

    def test_rejects_none_header(self):
        assert Json(STORE, SECRET).validate(None, "/x", "POST", "") is False


class TestConstruction:
    def test_rejects_empty_store_key(self):
        with pytest.raises(ValueError):
            Json("", SECRET)

    def test_rejects_empty_secret_key(self):
        with pytest.raises(ValueError):
            Json(STORE, "")

    def test_strips_keys(self):
        j = Json("  store  ", "  sec  ")
        assert j.store_key == "store"
        assert j.secret_key == "sec"
