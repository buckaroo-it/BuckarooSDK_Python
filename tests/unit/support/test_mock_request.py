"""Tests for tests.support.mock_request."""

from tests.support.mock_request import BuckarooMockRequest


def test_json_factory_stores_method_url_payload_status_headers():
    req = BuckarooMockRequest.json(
        "post",
        "https://x/json/Pay",
        {"ok": True},
        status=201,
        headers={"X-Test": "1"},
    )
    response = req.to_http_response()
    assert response.status_code == 201
    assert response.success is True
    assert response.headers["X-Test"] == "1"
    assert response.headers["Content-Type"] == "application/json"
    assert '"ok": true' in response.text


def test_exact_url_match():
    req = BuckarooMockRequest.json("POST", "https://x/json/Pay", {})
    assert req.matches("POST", "https://x/json/Pay") is True
    assert req.matches("POST", "https://x/json/Pay/extra") is False


def test_method_is_case_insensitive():
    req = BuckarooMockRequest.json("post", "https://x/a", {})
    assert req.matches("post", "https://x/a") is True
    assert req.matches("POST", "https://x/a") is True


def test_method_mismatch():
    req = BuckarooMockRequest.json("POST", "https://x/a", {})
    assert req.matches("GET", "https://x/a") is False


def test_wildcard_url_match():
    req = BuckarooMockRequest.json("POST", "*/json/Transaction*", {})
    assert req.matches("POST", "https://x/json/Transaction") is True
    assert req.matches("POST", "https://x/json/TransactionStatus") is True
    assert req.matches("POST", "https://x/other") is False


def test_regex_url_match():
    req = BuckarooMockRequest.json("POST", r"/^https:\/\/x\/.*\/Pay$/", {})
    assert req.matches("POST", "https://x/json/Pay") is True
    assert req.matches("POST", "https://x/json/Refund") is False


def test_mismatch_message_contains_expected_and_actual():
    req = BuckarooMockRequest.json("POST", "https://x/a", {})
    msg = req.mismatch_message("GET", "https://y/b")
    assert "POST https://x/a" in msg
    assert "GET https://y/b" in msg


def test_with_exception_returns_self_and_stores():
    err = RuntimeError("boom")
    req = BuckarooMockRequest.json("POST", "https://x/a", {})
    result = req.with_exception(err)
    assert result is req
    assert req.exception is err


def test_no_exception_by_default():
    req = BuckarooMockRequest.json("POST", "https://x/a", {})
    assert req.exception is None


def test_non_success_status_sets_success_false():
    req = BuckarooMockRequest.json("POST", "https://x/a", {"err": "bad"}, status=500)
    response = req.to_http_response()
    assert response.status_code == 500
    assert response.success is False


def test_custom_header_does_not_override_content_type_when_absent():
    req = BuckarooMockRequest.json("POST", "https://x/a", {}, headers={"X-Foo": "bar"})
    response = req.to_http_response()
    assert response.headers["X-Foo"] == "bar"
    assert response.headers["Content-Type"] == "application/json"
