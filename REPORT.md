# Test Suite Audit Report

**Date:** 2026-04-16
**Scope:** All ~100 test files in `tests/`
**Method:** Full read of every test file + corresponding source, then adversarial verification of each finding via skeptic agents.

Each finding was classified after verification as **CONFIRMED**, **EXAGGERATED** (partially true but overstated), or **RETRACTED** (wrong).

---

## HIGH — Tests That Would Pass on Broken Code

### 1. `TestHmacSensitivity` proves local helper, not client — EXAGGERATED

**File:** `tests/unit/http/test_client.py`
**Claim:** 6 tests never call the client with the mutated input.
**Verdict:** The tests call the client with the original input, extract the nonce, then use a local helper to derive what the mutated input would produce. The local helper is itself validated against the client's output in `TestHmacDeterminism` and `TestHmacVectors`, so the chain of trust holds. The approach is indirect but sound.

### 2. `test_http_url_strips_protocol_for_signing` uses different nonces — CONFIRMED

**File:** `tests/unit/http/test_client.py`, lines 391-404
**Detail:** Two separate calls produce two different nonces (`nonce_http` vs `nonce_https`). The test checks each signature against its own re-derivation but never compares `sig_http` to `sig_https` under a shared nonce. It proves internal consistency but not that http/https produce the same signature for the same path.

### 3. Three `test_false_when_*` tests assert `is True` — CONFIRMED

**File:** `tests/unit/http/test_response.py`, lines 127-150
**Detail:** `test_false_when_status_code_missing_from_status`, `test_false_when_status_is_falsy`, `test_false_when_data_is_empty_but_http_ok` all assert `is True`. The behavior is correct (HTTP 2xx with no Buckaroo status falls through to `self.success` which is True), but the names are inverted. Copy-paste naming error.

### 4. `test_get_config_info_excludes_sensitive_fields` tests absent fields — CONFIRMED

**File:** `tests/unit/test__buckaroo_client.py`, lines 266-285
**Detail:** Parametrized over 9 field names (`secretKey`, `token`, `password`, etc.) that `get_config_info()` never produces. The source returns a hardcoded dict with keys: `environment`, `api_endpoint`, `timeout`, `retry_attempts`, `api_version`, `logging_enabled`. All 9 assertions are vacuously true.

### 5. `test_http_strategy_argument_is_accepted_and_stored` asserts raw string — CONFIRMED

**File:** `tests/unit/test__buckaroo_client.py`, lines 122-123
**Detail:** Asserts `client.http_strategy == "requests"` (the raw string), not that a `RequestsStrategy` instance was resolved and wired up.

### 6. `test_get_available_methods_matches_factory` — EXAGGERATED

**File:** `tests/unit/services/test_solution_service.py`, lines 127-129
**Claim:** Compares factory to itself, tautological.
**Verdict:** It tests that `SolutionService` delegates to its factory instance. Since `get_available_methods` returns a static registry, the delegation is trivial; the test is low-value but not literally self-comparing. The companion tests checking specific methods and `is_method_supported` are the useful ones.

### 7. `is_successful()` never tested with real 190 status code — CONFIRMED

**File:** `tests/unit/models/test_payment_response.py`
**Detail:** `is_successful()` checks `self._raw_data.get('is_successful_payment', False)`. The only test (line 226-228) drives it via `{"is_successful_payment": True}`. The test at line 321-325 uses status code 190 but only asserts `is_pending/is_cancelled/is_failed` are False; it never asserts `is_successful() is True`. Design question: `is_successful` relies on a separate flag rather than the status code.

### 8. `test_smoke.py` weak assertions — EXAGGERATED

**File:** `tests/feature/test_smoke.py`
**Claim:** Both tests assert only `is not None`, proves nothing.
**Verdict:** There are four tests, not two. The first (`test_buckaroo_fixture_creates_payment_builder`) is genuinely weak. The second exercises mock plumbing end-to-end. The other two make structural assertions on helper output. "Proves nothing" is too strong; it proves fixture wiring works.

### 9. `xfail` test queues mock that leaks — CONFIRMED (with caveat)

**File:** `tests/feature/payments/test_external_payment.py`, lines 38-59
**Detail:** The `xfail(strict=True)` test queues a mock at line 40, then fails before consuming it. The feature `conftest.py`'s `_assert_mocks_consumed` runs on teardown unconditionally. However, pytest marks strict xfail tests that fail as "xfail" (expected), not "failed", so the teardown error may be swallowed under the xfail umbrella. The mock does leak in principle; the fixture design is inconsistent with the root conftest (which guards against this).

### 10. `test_payconiq` payFastCheckout/instantRefund — RETRACTED

**File:** `tests/feature/payments/test_payconiq.py`
**Claim:** Assert only `response is not None`.
**Verdict:** Wrong. `test_payconiq_instant_refund` (lines 44-64) asserts `response.status.code.code == 190` and `response.key == response_body["Key"]`. `test_payconiq_fast_checkout` (lines 66-81) asserts `response.is_pending()`, `response.get_redirect_url() is not None`, and `response.key == response_body["Key"]`. These are meaningful assertions.

---

## MEDIUM — Duplicate / Redundant Tests

### 11. `test_str_reflects_single_arg` duplicates `test_message_only_round_trip` — CONFIRMED

**File:** `tests/unit/exceptions/test__buckaroo_error.py`
**Detail:** Both test `str()` on a single-arg `BuckarooError` with different messages. Same behavior, zero new coverage.

### 12. `test_repr_*` pins CPython `Exception.__repr__` — CONFIRMED

**File:** `tests/unit/exceptions/test__buckaroo_error.py`
**Detail:** `BuckarooError` defines no `__repr__`. The tests pin CPython's built-in format, which could vary across Python implementations.

### 13. `test_constructor_args_round_trip` and `test_caught_by` — EXAGGERATED

**File:** `tests/unit/exceptions/test__authentication_error.py`
**Claim:** Both are tautological/redundant with `test_is_subclass`.
**Verdict:** `test_caught_by` tests actual `try/except` dispatch mechanics, not just MRO. `test_constructor_args_round_trip` verifies args propagate through the subclass. The distinction is minor but real. Redundancy claim is overstated.

### 14. `test_pay_spec_contains_mandate_field` fully duplicated by snapshot — CONFIRMED

**File:** `tests/unit/builders/payments/test_sepadirectdebit_builder.py`, lines 88-148
**Detail:** The snapshot test at lines 88-134 already asserts all four mandate fields with type and required. The parametrized test below re-checks the same four fields with identical assertions.

### 15. Two tests both assert `status_code == 500` — EXAGGERATED

**File:** `tests/feature/error_paths/test_server_error.py`
**Detail:** The `status_code == 500` assertion overlaps, but the first test's primary focus is `err.response is not None` while the second's is `response.success is False`. Not a true duplicate; partial overlap.

### 16. Second billink pay test adds no coverage — CONFIRMED

**File:** `tests/feature/payments/test_billink.py`
**Detail:** Both tests call `.pay()` and assert the same three things: `is_pending()`, `get_redirect_url() is not None`, `response.key`. Different article data is passed but never verified in the request payload. No new code path is exercised.

### 17. Two `createSubscription` tests assert identical things — EXAGGERATED

**File:** `tests/feature/solutions/test_subscription.py`
**Claim:** Near-duplicates.
**Verdict:** They exercise different input paths (dict params vs fluent builder), which is a legitimate distinction. The response assertions are identical, but the input-path coverage justifies two tests.

### 18. ~25 tests are conceptual twins across base_builder/payment_builder — CONFIRMED

**Files:** `tests/unit/builders/test_base_builder.py`, `tests/unit/builders/payments/test_payment_builder.py`
**Detail:** The test_base_builder docstring acknowledges PaymentBuilder "shadows nearly every BaseBuilder method with an identical copy." Roughly 20-25 conceptual duplicates exist. Intentional (different MRO), but generates significant noise.

---

## MEDIUM — Weak Assertions / Missing Key Checks

### 19. 5 creditcard encrypted/token tests missing `response.key` — CONFIRMED

**File:** `tests/feature/payments/test_creditcard.py`, lines 89-186
**Detail:** `test_creditcard_pay_encrypted`, `test_creditcard_pay_with_security_code`, `test_creditcard_pay_with_token`, `test_creditcard_authorize_encrypted`, `test_creditcard_authorize_with_token` all assert `is_pending()` and `get_redirect_url() is not None` but none check `response.key`. Every other test in the same file does the key check.

### 20. `test_riverty` missing key assertion — CONFIRMED

**File:** `tests/feature/payments/test_riverty.py`
**Detail:** Asserts `is_pending()` and `get_redirect_url() is not None` but never `response.key`.

### 21. `test_sepadirectdebit` only `is_pending()` — CONFIRMED

**File:** `tests/feature/payments/test_sepadirectdebit.py`, line 26
**Detail:** Only assertion is `response.is_pending()`. No redirect URL check, no key check.

### 22. Default solution: refund missing key, service-name test weak — CONFIRMED

**File:** `tests/feature/solutions/test_default_solution.py`
**Detail:** Refund test asserts `status.code.code == 190` but not `response.key`. Service-name-from-payload test only asserts `response.is_pending()`; never verifies the outgoing request's service name was `"custommethod"`.

### 23. Voucher case-insensitive test asserts `!= {}` only — CONFIRMED

**File:** `tests/unit/builders/payments/test_buckaroo_voucher_builder.py`, lines 100-107
**Detail:** Only checks `allowed != {}`. If the source accidentally swapped specs between actions, this test would still pass.

### 24. External payment round-trip tests only check `isinstance` — CONFIRMED

**File:** `tests/unit/builders/payments/test_external_payment_builder.py`, lines 112-186
**Detail:** Both `test_pay_round_trips` and `test_refund_round_trips` assert `isinstance(response, PaymentResponse)` and `mock_strategy.assert_all_consumed()` but never check `response.key`, status, or any response content.

---

## MEDIUM — Source Bugs Masked by Tests

### 25. KlarnaKP dead code on second if-block — CONFIRMED

**File:** `buckaroo/builders/payments/klarnakp_builder.py`, lines 37 and 51
**Detail:** Line 37: `if action.lower() in ["pay", "cancelreservation"]` returns early. Line 51: `if action.lower() in ["pay", "cancelreservation", "extendreservation"]` — the `"pay"` and `"cancelreservation"` branches are dead because they were already returned from line 37. Only `"extendreservation"` is reachable via line 51. The dead code means `extendReservation` coincidentally returns the correct spec, but the intent was probably to combine all three into one block. A refactor removing line 51 would silently break `ExtendReservation`.

### 26. Logging observer pins known masking bug without `xfail` — CONFIRMED

**File:** `tests/unit/observers/test_logging_observer.py`, lines 74-104
**Detail:** `test_deep_buckaroo_shape_parameters_list` pins the behavior where `"CARD-SECRET"` passes through unmasked because the masker checks dict keys, not nested `"Value"` fields. The docstring says "gap noted for a future issue" but the test asserts the broken behavior as correct rather than using `@pytest.mark.xfail`.

### 27. `test_timeout_none_interpolates_literal_none_in_message` — CONFIRMED

**File:** `tests/unit/http/strategies/test_requests_strategy.py`, lines 308-318
**Detail:** Asserts `str(excinfo.value) == "Request timeout after None seconds"`. This pins a broken message where `None` is interpolated as a literal string instead of being handled (e.g., "no timeout configured" or raising a different error).

### 28. Parameter validation error messages grammatically inconsistent — CONFIRMED

**File:** `tests/unit/exceptions/test__parameter_validation_error.py`
**Detail:** Tests pin messages like `"Required parameter 'issuer' is missing Pay action"` (no "for" prefix) vs `"...is missing for ideal"` (with "for" prefix). The inconsistency is in the source's string formatting, and the tests faithfully reproduce it.

### 29. Klarna builder snapshot contains "Riverty articles" — CONFIRMED

**File:** `buckaroo/builders/payments/klarna_builder.py`, line 18
**Detail:** The `article` parameter description says `"Riverty articles"` — a copy-paste from `RivertyBuilder`. The test faithfully reproduces this source-level bug.

---

## LOW — Missing Coverage

### 30. No refund tests for IdealQR, PayPal, Trustly; no cancel for Transfer — CONFIRMED

**Files:** `tests/feature/payments/test_idealqr.py`, `test_paypal.py`, `test_trustly.py`, `test_transfer.py`
**Detail:** Each has only a single `test_*_pay_returns_pending_with_redirect` test. No refund/cancel tests despite the builders supporting these capabilities.

### 31. Only 401 tested in error paths, no 403 — CONFIRMED

**File:** `tests/feature/error_paths/test_auth_failure.py`
**Detail:** Single test for 401. No 403 scenario, which a misconfigured store key could produce.

### 32. Transfer pay snapshot checks 3 of 7 source fields — CONFIRMED

**Files:** `tests/unit/builders/payments/test_transfer_builder.py` (lines 90-95), `buckaroo/builders/payments/transfer_builder.py` (lines 15-23)
**Detail:** Source defines 7 fields: `customeremail`, `customerfirstname`, `customerlastname`, `customergender`, `sendmail`, `dateDue`, `customerCountry`. Test only checks `customeremail`, `customerfirstname`, `customerlastname`.

### 33. Credit card dynamic brand never verified in built request — CONFIRMED

**File:** `tests/unit/builders/payments/test_credit_card_builder.py`
**Detail:** `test_returns_brand_from_payload_when_present` (line 75-78) sets `brand` and checks `get_service_name() == "Visa"`. But no test verifies the brand flows through to the actual built/sent request payload's service name field. The unit test only covers `get_service_name()` in isolation.

### 34. Subscription tests exercise non-canonical action — CONFIRMED

**File:** `tests/unit/builders/solutions/test_subscription_builder.py`, lines 36-50
**Detail:** `test_get_allowed_service_parameters_pay_snapshot` tests `"Pay"` which returns `{}`. The subscription builder's canonical action is `CreateSubscription`. No test passes `"CreateSubscription"` to `get_allowed_service_parameters`. The `test_get_allowed_service_parameters_non_pay_returns_empty` parametrizes over `["Refund", "Capture", "Authorize", "UnknownAction"]` but not `"CreateSubscription"`.

---

## LOW — Inconsistencies

### 35. Voucher uses `not hasattr` instead of `not in __dict__` — CONFIRMED

**File:** `tests/unit/builders/payments/test_voucher_builder.py`, line 38
**Detail:** Uses `assert not hasattr(VoucherBuilder, "_serviceName")` while every other builder test uses `"_serviceName" not in BuilderClass.__dict__`. Semantically different: `hasattr` walks the MRO, `__dict__` checks only the class. Current behavior is equivalent but the inconsistency is a trap if a parent ever declares `_serviceName`.

### 36. Dead `mock` variable in payment_builder tests — CONFIRMED

**File:** `tests/unit/builders/payments/test_payment_builder.py`, lines 659-679
**Detail:** `test_post_transaction_returns_empty_payment_response_when_client_returns_none` and `test_post_data_request_returns_empty_payment_response_when_client_returns_none` both assign `mock, client = wire_recording_http()` then immediately monkey-patch `client.http_client.post`, never using `mock`.

### 37. Local `clean_env` duplicates autouse `_clean_buckaroo_env` — CONFIRMED

**Files:** `tests/unit/observers/test_logging_observer.py` (line 452), `tests/unit/conftest.py` (line 19)
**Detail:** The conftest's `_clean_buckaroo_env` is autouse and cleans all 9 `BUCKAROO_*` env vars. The local `clean_env` fixture cleans only the 4 logging-related vars. Since the autouse fixture already runs, the local one is redundant for deletion purposes. It's kept for its `return monkeypatch` chaining pattern, which the autouse fixture doesn't provide. Partially redundant, not fully.

### 38. Billink uses `isinstance` instead of `issubclass` — CONFIRMED

**File:** `tests/unit/builders/payments/test_billink_builder.py`, line 111
**Detail:** Uses `assert not isinstance(builder, capability)` on an instance, while every other file uses `issubclass(BuilderClass, capability)`. Functionally equivalent for this use case but inconsistent with the rest of the suite.

---

## Summary

| Severity | Confirmed | Exaggerated | Retracted | Total |
|----------|-----------|-------------|-----------|-------|
| HIGH     | 6         | 3           | 1         | 10    |
| MEDIUM (dupes) | 4  | 3           | 0         | 7     |
| MEDIUM (weak)  | 6  | 0           | 0         | 6     |
| MEDIUM (source bugs) | 5 | 0      | 0         | 5     |
| LOW (coverage) | 5   | 0           | 0         | 5     |
| LOW (style)    | 4   | 0           | 0         | 4     |
| **Total**      | **30** | **6**   | **1**     | **37** |

### Top 5 Actionable Items

1. **Fix KlarnaKP dead code** (#25) — merge lines 37 and 51 into one `if` block covering `["pay", "cancelreservation", "extendreservation"]`.
2. **Add `response.key` assertions** (#19-22) — 8 feature tests across creditcard, riverty, sepadirectdebit, and default_solution are missing the one assertion that ties response to mock.
3. **Fix `test_false_when_*` naming** (#3) — three test names say "false" but assert True.
4. **Remove vacuous `excludes_sensitive_fields` test** (#4) — parametrized over field names the source never produces.
5. **Mark masking gap as `xfail`** (#26) — `test_deep_buckaroo_shape_parameters_list` pins broken behavior; should use `@pytest.mark.xfail` until the masker is fixed.
