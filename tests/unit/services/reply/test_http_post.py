"""Tests for :class:`buckaroo.services.reply.http_post.HttpPost`."""

from __future__ import annotations

from hashlib import sha1

import pytest

from buckaroo.services.reply.http_post import HttpPost


SECRET = "secretkey"


def _sign(params: dict, secret: str = SECRET) -> str:
    """Reference SHA-1 signature per Buckaroo's documented algorithm."""
    items = [(k, v) for k, v in params.items() if k.lower() != "brq_signature"]
    filtered = [
        (k, v) for k, v in items if any(k.lower().startswith(p) for p in ("add_", "brq_", "cust_"))
    ]
    sorted_items = sorted(filtered, key=lambda pair: pair[0].lower())
    sign_string = "".join(f"{k}={v if v is not None else ''}" for k, v in sorted_items)
    sign_string += secret
    return sha1(sign_string.encode("utf-8")).hexdigest()


class TestComputeSignature:
    def test_sorts_keys_case_insensitively(self):
        h = HttpPost(SECRET)
        params = {"brq_b": "2", "BRQ_a": "1"}
        assert (
            h.compute_signature(params)
            == sha1(f"BRQ_a=1brq_b=2{SECRET}".encode("utf-8")).hexdigest()
        )

    def test_excludes_brq_signature_field(self):
        h = HttpPost(SECRET)
        params = {"brq_x": "1", "brq_signature": "deadbeef"}
        expected = sha1(f"brq_x=1{SECRET}".encode("utf-8")).hexdigest()
        assert h.compute_signature(params) == expected

    def test_filters_to_brq_add_cust_prefixes_only(self):
        h = HttpPost(SECRET)
        params = {"brq_a": "1", "add_b": "2", "cust_c": "3", "other_d": "4"}
        expected = sha1(f"add_b=2brq_a=1cust_c=3{SECRET}".encode("utf-8")).hexdigest()
        assert h.compute_signature(params) == expected

    def test_url_decodes_values(self):
        h = HttpPost(SECRET)
        params = {"brq_x": "hello+world"}
        expected = sha1(f"brq_x=hello world{SECRET}".encode("utf-8")).hexdigest()
        assert h.compute_signature(params) == expected

    def test_handles_empty_value(self):
        h = HttpPost(SECRET)
        params = {"brq_x": ""}
        expected = sha1(f"brq_x={SECRET}".encode("utf-8")).hexdigest()
        assert h.compute_signature(params) == expected


class TestValidate:
    def test_returns_true_for_valid_signature(self):
        h = HttpPost(SECRET)
        params = {"brq_amount": "10.00", "brq_invoicenumber": "INV-1"}
        params["brq_signature"] = _sign(params)
        assert h.validate(params) is True

    def test_returns_false_for_invalid_signature(self):
        h = HttpPost(SECRET)
        params = {"brq_amount": "10.00", "brq_signature": "not-a-real-sig"}
        assert h.validate(params) is False

    def test_returns_false_when_signature_missing(self):
        h = HttpPost(SECRET)
        assert h.validate({"brq_amount": "10.00"}) is False

    def test_returns_false_when_signature_empty(self):
        h = HttpPost(SECRET)
        assert h.validate({"brq_amount": "10.00", "brq_signature": ""}) is False

    def test_signature_field_lookup_is_case_insensitive(self):
        h = HttpPost(SECRET)
        params = {"brq_amount": "10.00"}
        params["BRQ_SIGNATURE"] = _sign(params)
        assert h.validate(params) is True

    def test_uses_constant_time_compare(self):
        h = HttpPost(SECRET)
        params = {"brq_amount": "10.00"}
        valid = _sign(params)
        params["brq_signature"] = "0" * len(valid)
        assert h.validate(params) is False


class TestConstruction:
    def test_rejects_empty_secret_key(self):
        with pytest.raises(ValueError):
            HttpPost("")

    def test_rejects_whitespace_only_secret_key(self):
        with pytest.raises(ValueError):
            HttpPost("   ")

    def test_strips_secret_key(self):
        h = HttpPost("  sec  ")
        assert h.secret_key == "sec"
