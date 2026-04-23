"""Shared HMAC-signing vectors for :mod:`tests.unit.http.test_client`.

The ``hmac_vectors`` fixture supplies tuples that pin the byte-for-byte
derivation performed by ``BuckarooHttpClient._generate_hmac_signature``.

Vector shape::

    (label, store_key, secret_key, method, url, content, timestamp,
     nonce, expected_encoded_url, expected_content_b64, expected_signature)

Only ``nonce`` is unobservable when calling the client (UUID4 is generated
internally). Tests parse the nonce out of the returned ``Authorization``
header, then re-derive the signature and compare against
``expected_signature`` using the vector's fixed nonce equivalent — or, more
practically, assert the client's signature matches a locally recomputed one
using the parsed nonce. The fixed-nonce ``expected_signature`` is the
canonical byte check for the derivation formula itself.

Sources
-------
Vectors are Python-only, frozen 2026-04-15. PHP byte-level parity requires
encoder alignment (PHP ``urlencode`` encodes space as ``+`` whereas Python
``urllib.parse.quote`` uses ``%20``; PHP ``JSON_PRESERVE_ZERO_FRACTION``
keeps ``10.0`` as ``10.0`` while ``json.dumps`` drops it to ``10``). See
Epic 3 notes. ASCII-URL + integer-amount inputs are structurally identical
between SDKs and line up with
``BuckarooSDK_PHP/tests/Unit/Handlers/HMAC/GeneratorTest.php::``
``test_generates_deterministic_hmac_with_fixed_nonce_and_timestamp``; we
still freeze the Python output here since PHP is not executed in this
suite.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def hmac_vectors():
    """Return frozen HMAC derivation vectors.

    Each tuple is::

        (label, store_key, secret_key, method, url, content, timestamp,
         nonce, expected_encoded_url, expected_content_b64,
         expected_signature)
    """
    return [
        # 1. POST, empty body, canonical Buckaroo endpoint. Structurally
        #    matches PHP test_generates_deterministic_hmac_with_fixed_nonce_and_timestamp
        #    (ASCII URL, no JSON body) — signature frozen from Python.
        (
            "post_empty_body",
            "test_website_key",
            "secret_key_123",
            "POST",
            "https://testcheckout.buckaroo.nl/json/Transaction",
            "",
            "1234567890",
            "test-nonce-12345",
            "testcheckout.buckaroo.nl%2fjson%2ftransaction",
            "",
            "9ibLr6D5q3R23p0BHD9d0Zw/kftvz4O81+cCotkPX0c=",
        ),
        # 2. POST, raw string body. PHP's base64Data() short-circuits strings
        #    through md5() with no JSON encoding; Python treats the body
        #    as-is. Both SDKs therefore agree on content digest for pure
        #    strings. Frozen from Python.
        (
            "post_string_body",
            "test_website_key",
            "secret_key_123",
            "POST",
            "https://testcheckout.buckaroo.nl/json/Transaction",
            "raw-string-data",
            "1234567890",
            "test-nonce-12345",
            "testcheckout.buckaroo.nl%2fjson%2ftransaction",
            "w/j4rjsN8ba7EffGylXjVQ==",
            "U6/pxRfIFH8xgZDq3VaNA82YHPtxHxWJvYMayYIJF94=",
        ),
        # 3. POST, integer-amount JSON body. Because the amount is int (10),
        #    Python json.dumps and PHP json_encode with
        #    JSON_PRESERVE_ZERO_FRACTION produce identical bytes
        #    (`{"amount":10,"currency":"EUR"}`). Still frozen from Python.
        (
            "post_json_int_amount",
            "test_website_key",
            "secret_key_123",
            "POST",
            "https://testcheckout.buckaroo.nl/json/Transaction",
            '{"amount":10,"currency":"EUR"}',
            "1234567890",
            "test-nonce-12345",
            "testcheckout.buckaroo.nl%2fjson%2ftransaction",
            "7ZsdtWbYvIvtRjqRuBI4kw==",
            "GWYW3Jco2spWn9ePsKOd52SCbPyjVaAz8cvLljY/5mw=",
        ),
        # 4. POST, UTF-8 body with CJK codepoints. Python json.dumps with
        #    ensure_ascii=False matches PHP JSON_UNESCAPED_UNICODE for the
        #    raw string we feed in. Python-only frozen output.
        (
            "post_json_unicode",
            "test_website_key",
            "secret_key_123",
            "POST",
            "https://example.com/api",
            '{"description":"Payment 支付","amount":15}',
            "1234567890",
            "test-nonce-12345",
            "example.com%2fapi",
            "m2G/qZLlxSuH0IXNIBo6/g==",
            "sshs5MG1ucciAE2hmnSLDtgZfJYYLq3BioewtUWEI+0=",
        ),
        # 5. GET, empty body — exercises method sensitivity in string_to_sign.
        (
            "get_empty_body",
            "test_website_key",
            "secret_key_123",
            "GET",
            "https://example.com/api",
            "",
            "1234567890",
            "test-nonce-12345",
            "example.com%2fapi",
            "",
            "emiJMhAQGfao80k4kplOqZscCC0kZ9a1h6FhBIixQtE=",
        ),
        # 6. POST, mixed-case host and path. The Python quote(...).lower()
        #    must lowercase after percent-encoding. Python-only; PHP would
        #    encode spaces as '+' (not used here), so ASCII-only URL keeps
        #    the SDKs aligned on this vector.
        (
            "post_mixedcase_url",
            "test_website_key",
            "secret_key_123",
            "POST",
            "http://API.Example.COM/Path",
            "",
            "1234567890",
            "test-nonce-12345",
            "api.example.com%2fpath",
            "",
            "v+djuZQm7pGRteROmd9VtvkRE8AqtqXdYp0Sa1ERyT4=",
        ),
    ]
