"""Tests for buckaroo.observers.logging_observer masking behaviour."""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler

import pytest

from buckaroo.observers.logging_observer import (
    BuckarooLoggingObserver,
    ContextualLoggingObserver,
    LogConfig,
    LogDestination,
    LogLevel,
    create_logger,
    create_logger_from_env,
)


def _observer(mask: bool = True) -> BuckarooLoggingObserver:
    """Build an observer that doesn't write to disk during tests."""
    config = LogConfig(destination=LogDestination.STDOUT, mask_sensitive_data=mask)
    return BuckarooLoggingObserver(config)


# --- Sensitive-field set ---


@pytest.mark.parametrize(
    "field",
    [
        "secret_key",
        "password",
        "token",
        "authorization",
        "cvv",
        "cardnumber",
        "card_number",
        "iban",
        "account_number",
        # New Buckaroo-specific entries added in this issue:
        "cvc",
        "bic",
        "pan",
        "expirydate",
        "encryptedcarddata",
    ],
)
def test_sensitive_fields_contains_expected_entries(field):
    obs = _observer()
    assert field in obs._sensitive_fields


# --- Masking matrix ---


@pytest.mark.parametrize(
    "key",
    [
        "cvc",
        "bic",
        "pan",
        "expirydate",
        "encryptedcarddata",
        "CVC",
        "Bic",
        "PAN",
        "ExpiryDate",
        "EncryptedCardData",
    ],
)
def test_new_sensitive_keys_are_masked_top_level(key):
    obs = _observer()
    masked = obs._mask_sensitive_data({key: "raw-value"})
    assert masked[key] == "***MASKED***"


def test_nested_dict_masks_sensitive_key():
    obs = _observer()
    result = obs._mask_sensitive_data({"outer": {"cvc": "123", "description": "ok"}})
    assert result["outer"]["cvc"] == "***MASKED***"
    assert result["outer"]["description"] == "ok"


def test_list_of_dicts_masks_sensitive_key():
    obs = _observer()
    result = obs._mask_sensitive_data(
        [
            {"bic": "ABNANL2A", "amount": 10},
            {"pan": "4111...", "currency": "EUR"},
        ]
    )
    assert result[0]["bic"] == "***MASKED***"
    assert result[0]["amount"] == 10
    assert result[1]["pan"] == "***MASKED***"
    assert result[1]["currency"] == "EUR"


def test_deep_buckaroo_shape_parameters_list():
    """Deep Buckaroo payload: Services.ServiceList[].Parameters[].Name/Value.

    The masker inspects dict KEYS for the ***MASKED*** path and string VALUES
    for the ***POTENTIALLY_SENSITIVE*** fallback. The Name "encryptedCardData"
    is a *value* containing a sensitive substring, so it gets POTENTIALLY_SENSITIVE.
    The paired Value is covered by ``test_deep_buckaroo_shape_parameters_value_is_masked``.
    """
    obs = _observer()
    payload = {
        "Services": {
            "ServiceList": [
                {
                    "Name": "creditcard",
                    "Parameters": [{"Name": "encryptedCardData", "Value": "CARD-SECRET"}],
                }
            ]
        },
        "encryptedCardData": "ALSO-SECRET",
    }
    result = obs._mask_sensitive_data(payload)
    # Top-level sensitive key is masked.
    assert result["encryptedCardData"] == "***MASKED***"
    param = result["Services"]["ServiceList"][0]["Parameters"][0]
    # Name is a value containing a sensitive substring → POTENTIALLY_SENSITIVE.
    assert param["Name"] == "***POTENTIALLY_SENSITIVE***"


def test_deep_buckaroo_shape_parameters_value_is_masked():
    """The Value field paired with a sensitive Name like 'encryptedCardData'
    is masked via the Name/Value pair detection."""
    obs = _observer()
    payload = {
        "Services": {
            "ServiceList": [
                {
                    "Name": "creditcard",
                    "Parameters": [{"Name": "encryptedCardData", "Value": "CARD-SECRET"}],
                }
            ]
        },
    }
    result = obs._mask_sensitive_data(payload)
    param = result["Services"]["ServiceList"][0]["Parameters"][0]
    assert param["Value"] == "***MASKED***"


def test_name_value_pair_without_sensitive_name_passes_through():
    """A dict with Name/Value where Name is not sensitive leaves Value intact."""
    obs = _observer()
    result = obs._mask_sensitive_data({"Name": "amount", "Value": "42"})
    assert result["Value"] == "42"


def test_name_value_pair_with_non_string_name_passes_through():
    """A dict with a non-string Name skips the sensitive pair check."""
    obs = _observer()
    result = obs._mask_sensitive_data({"Name": 123, "Value": "data"})
    assert result["Value"] == "data"


# --- JSON string input ---


def test_format_json_parses_json_string_and_masks():
    obs = _observer()
    raw = json.dumps({"cvc": "999", "amount": 10})
    out = obs._format_json(raw)
    parsed = json.loads(out)
    assert parsed["cvc"] == "***MASKED***"
    assert parsed["amount"] == 10


def test_format_json_non_json_string_returned_verbatim():
    obs = _observer()
    assert obs._format_json("not json at all") == "not json at all"


def test_format_json_dict_input_produces_masked_json():
    obs = _observer()
    out = obs._format_json({"pan": "4111", "currency": "EUR"})
    parsed = json.loads(out)
    assert parsed["pan"] == "***MASKED***"
    assert parsed["currency"] == "EUR"


def test_format_json_non_serialisable_falls_back_to_str():
    class NotJSON:
        def __repr__(self):
            return "<NotJSON>"

    obs = _observer()
    # json.dumps handles most things via default=str; force a failure by
    # triggering an exception path — a dict with a non-serialisable key
    # (keys must be str/int/float/bool/None) raises TypeError.
    weird = {object(): "value"}
    result = obs._format_json(weird)
    assert isinstance(result, str)
    assert result == str(weird)


# --- Case-insensitive substring matching ---


@pytest.mark.parametrize(
    "key",
    [
        "Authorization",
        "AUTHORIZATION",
        "card_Number",
        "EncryptedCardData",
        "X-Authorization-Header",  # substring match
    ],
)
def test_case_insensitive_substring_match(key):
    obs = _observer()
    result = obs._mask_sensitive_data({key: "secret"})
    assert result[key] == "***MASKED***"


# --- Sentinel non-sensitive fields pass through ---


@pytest.mark.parametrize(
    "key,value",
    [
        ("description", "Order 42"),
        ("amount", 100.50),
        ("currency", "EUR"),
    ],
)
def test_non_sensitive_fields_pass_through(key, value):
    obs = _observer()
    result = obs._mask_sensitive_data({key: value})
    assert result[key] == value


# --- String values with sensitive keyword ---


def test_string_with_sensitive_keyword_is_redacted():
    obs = _observer()
    # A bare string value that *contains* a sensitive keyword gets the
    # POTENTIALLY_SENSITIVE treatment.
    assert obs._mask_sensitive_data("this has a cvc in it") == "***POTENTIALLY_SENSITIVE***"


def test_string_without_sensitive_keyword_passes_through():
    obs = _observer()
    assert obs._mask_sensitive_data("harmless log line") == "harmless log line"


# --- Disable masking ---


def test_masking_disabled_returns_data_unchanged():
    obs = _observer(mask=False)
    data = {"cvc": "999", "password": "hunter2", "encryptedCardData": "x"}
    assert obs._mask_sensitive_data(data) == data


# --- log_request ---


def test_log_request_emits_one_info_record_with_method_url_masked_headers_and_body(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_request(
        "POST",
        "https://checkout.buckaroo.nl/json/Transaction",
        headers={"Authorization": "hmac topsecret", "Content-Type": "application/json"},
        body={"cvc": "999", "amount": 10},
    )
    records = [r for r in caplog.records if r.name == "buckaroo_sdk"]
    assert len(records) == 1
    rec = records[0]
    assert rec.levelno == logging.INFO
    assert "POST" in rec.message
    assert "https://checkout.buckaroo.nl/json/Transaction" in rec.message
    assert "***MASKED***" in rec.message
    assert "topsecret" not in rec.message
    assert "999" not in rec.message


# --- log_response ---


@pytest.mark.parametrize(
    "status,expected_level",
    [
        (200, logging.INFO),
        (201, logging.INFO),
        (299, logging.INFO),
        (400, logging.WARNING),
        (404, logging.WARNING),
        (499, logging.WARNING),
        (500, logging.ERROR),
        (503, logging.ERROR),
    ],
)
def test_log_response_level_matches_status_code(caplog, status, expected_level):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_response(status, headers={"X-Trace": "abc"}, body={"ok": True})
    records = [r for r in caplog.records if r.name == "buckaroo_sdk"]
    assert len(records) == 1
    assert records[0].levelno == expected_level


def test_log_response_includes_duration_when_provided(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_response(200, duration_ms=123.456)
    records = [r for r in caplog.records if r.name == "buckaroo_sdk"]
    assert len(records) == 1
    assert "123.46" in records[0].message
    assert "ms" in records[0].message


def test_log_response_omits_duration_when_not_provided(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_response(200)
    records = [r for r in caplog.records if r.name == "buckaroo_sdk"]
    assert "Duration" not in records[0].message


# --- log_exception ---


def test_log_exception_emits_error(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_exception(ValueError("boom"), context={"step": "validate"})
    records = [r for r in caplog.records if r.name == "buckaroo_sdk"]
    assert len(records) == 1
    rec = records[0]
    assert rec.levelno == logging.ERROR
    assert "ValueError" in rec.message
    assert "boom" in rec.message


def test_log_exception_includes_stack_trace_when_logger_at_debug(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = BuckarooLoggingObserver(
        LogConfig(level=LogLevel.DEBUG, destination=LogDestination.STDOUT)
    )
    try:
        raise RuntimeError("kaboom")
    except RuntimeError as exc:
        obs.log_exception(exc)
    records = [r for r in caplog.records if r.name == "buckaroo_sdk"]
    assert len(records) == 1
    assert "Stack Trace" in records[0].message
    assert "RuntimeError" in records[0].message


def test_log_exception_includes_kwargs_as_additional_info(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_exception(ValueError("boom"), request_id="req-9", attempt=2)
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert "Additional Info" in rec.message
    assert "req-9" in rec.message
    assert "2" in rec.message


def test_log_payment_operation_minimal_omits_amount_currency_and_details(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_payment_operation("create", "ideal")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert "Amount" not in rec.message
    assert "Currency" not in rec.message
    assert "Details" not in rec.message


def test_log_exception_omits_stack_trace_when_logger_above_debug(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = BuckarooLoggingObserver(LogConfig(level=LogLevel.INFO, destination=LogDestination.STDOUT))
    try:
        raise RuntimeError("kaboom")
    except RuntimeError as exc:
        obs.log_exception(exc)
    records = [r for r in caplog.records if r.name == "buckaroo_sdk"]
    assert "Stack Trace" not in records[0].message


# --- log_payment_operation / log_config_change / log_info family ---


def test_log_payment_operation_masks_sensitive_kwargs(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_payment_operation(
        "execute",
        "creditcard",
        amount=42.0,
        currency="EUR",
        cvc="999",
        token="tok-123",
    )
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert rec.levelno == logging.INFO
    assert "execute" in rec.message
    assert "creditcard" in rec.message
    assert "***MASKED***" in rec.message
    assert "999" not in rec.message
    assert "tok-123" not in rec.message


def test_log_config_change_masks_sensitive_values(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    # `_mask_sensitive_data` redacts string values that *contain* a sensitive
    # keyword. Use values containing "cvc" so the masker fires on the value.
    obs.log_config_change("payment_field", "old cvc value", "new cvc value")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert rec.levelno == logging.INFO
    assert "***POTENTIALLY_SENSITIVE***" in rec.message
    assert "old cvc value" not in rec.message
    assert "new cvc value" not in rec.message


def test_log_config_change_with_extra_context(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_config_change("timeout", 10, 30, source="env")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert "timeout" in rec.message
    assert "env" in rec.message


@pytest.mark.parametrize(
    "method,expected_level",
    [
        ("log_info", logging.INFO),
        ("log_debug", logging.DEBUG),
        ("log_warning", logging.WARNING),
        ("log_error", logging.ERROR),
    ],
)
def test_log_info_family_masks_sensitive_kwargs(caplog, method, expected_level):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = BuckarooLoggingObserver(
        LogConfig(level=LogLevel.DEBUG, destination=LogDestination.STDOUT)
    )
    getattr(obs, method)("processing", cvc="999", request_id="req-1")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert rec.levelno == expected_level
    assert "processing" in rec.message
    assert "req-1" in rec.message
    assert "999" not in rec.message
    assert "***MASKED***" in rec.message


def test_log_info_without_kwargs_has_no_context_block(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    obs = _observer()
    obs.log_info("hello")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert rec.message == "hello"


# --- LogConfig defaults ---


def test_log_config_defaults():
    cfg = LogConfig()
    assert cfg.level is LogLevel.INFO
    assert cfg.destination is LogDestination.BOTH
    assert cfg.log_file == "buckaroo_sdk.log"
    assert cfg.max_file_size == 10 * 1024 * 1024
    assert cfg.backup_count == 5
    assert cfg.mask_sensitive_data is True


# --- LogDestination handler installation ---


def test_destination_stdout_installs_only_stream_handler():
    obs = BuckarooLoggingObserver(LogConfig(destination=LogDestination.STDOUT))
    handlers = obs.logger.handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)
    assert not isinstance(handlers[0], RotatingFileHandler)
    assert handlers[0].stream is sys.stdout


def test_destination_file_installs_only_rotating_file_handler(tmp_path):
    log_path = str(tmp_path / "test.log")
    obs = BuckarooLoggingObserver(LogConfig(destination=LogDestination.FILE, log_file=log_path))
    handlers = obs.logger.handlers
    assert len(handlers) == 1
    assert isinstance(handlers[0], RotatingFileHandler)


def test_destination_both_installs_stream_and_rotating_file_handlers(tmp_path):
    log_path = str(tmp_path / "test.log")
    obs = BuckarooLoggingObserver(LogConfig(destination=LogDestination.BOTH, log_file=log_path))
    handler_types = {type(h) for h in obs.logger.handlers}
    assert RotatingFileHandler in handler_types
    # The non-rotating handler is a StreamHandler pointed at stdout.
    stream_handlers = [
        h
        for h in obs.logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
    ]
    assert len(stream_handlers) == 1
    assert stream_handlers[0].stream is sys.stdout


# --- create_logger ---


def test_create_logger_builds_configured_observer(tmp_path):
    log_path = str(tmp_path / "configured.log")
    obs = create_logger(level=LogLevel.WARNING, destination=LogDestination.FILE, log_file=log_path)
    assert isinstance(obs, BuckarooLoggingObserver)
    assert obs.config.level is LogLevel.WARNING
    assert obs.config.destination is LogDestination.FILE
    assert obs.config.log_file == log_path


def test_create_logger_passes_through_extra_kwargs(tmp_path):
    log_path = str(tmp_path / "extra.log")
    obs = create_logger(
        destination=LogDestination.FILE,
        log_file=log_path,
        mask_sensitive_data=False,
        backup_count=2,
    )
    assert obs.config.mask_sensitive_data is False
    assert obs.config.backup_count == 2


# --- create_logger_from_env ---


# Kept despite autouse _clean_buckaroo_env — returns monkeypatch for .setenv() chaining in tests.
@pytest.fixture
def clean_env(monkeypatch):
    for var in (
        "BUCKAROO_LOG_LEVEL",
        "BUCKAROO_LOG_DESTINATION",
        "BUCKAROO_LOG_FILE",
        "BUCKAROO_LOG_MASK_SENSITIVE",
    ):
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


def test_create_logger_from_env_uses_defaults_when_no_env_vars(clean_env):
    obs = create_logger_from_env()
    assert obs.config.level is LogLevel.INFO
    assert obs.config.destination is LogDestination.BOTH
    assert obs.config.log_file == "buckaroo_sdk.log"
    assert obs.config.mask_sensitive_data is True


def test_create_logger_from_env_reads_valid_env_vars(clean_env, tmp_path):
    log_path = str(tmp_path / "env.log")
    clean_env.setenv("BUCKAROO_LOG_LEVEL", "DEBUG")
    clean_env.setenv("BUCKAROO_LOG_DESTINATION", "stdout")
    clean_env.setenv("BUCKAROO_LOG_FILE", log_path)
    clean_env.setenv("BUCKAROO_LOG_MASK_SENSITIVE", "true")
    obs = create_logger_from_env()
    assert obs.config.level is LogLevel.DEBUG
    assert obs.config.destination is LogDestination.STDOUT
    assert obs.config.log_file == log_path
    assert obs.config.mask_sensitive_data is True


def test_create_logger_from_env_invalid_destination_falls_back_to_both(clean_env):
    clean_env.setenv("BUCKAROO_LOG_DESTINATION", "invalid")
    obs = create_logger_from_env()
    assert obs.config.destination is LogDestination.BOTH


def test_create_logger_from_env_invalid_level_falls_back_to_info(clean_env):
    clean_env.setenv("BUCKAROO_LOG_LEVEL", "NONSENSE")
    obs = create_logger_from_env()
    assert obs.config.level is LogLevel.INFO


def test_create_logger_from_env_mask_false_disables_masking(clean_env):
    clean_env.setenv("BUCKAROO_LOG_MASK_SENSITIVE", "false")
    obs = create_logger_from_env()
    assert obs.config.mask_sensitive_data is False


# --- File rotation ---


def test_rotating_file_handler_rolls_at_max_file_size(tmp_path):
    log_path = tmp_path / "rotate.log"
    obs = BuckarooLoggingObserver(
        LogConfig(
            destination=LogDestination.FILE,
            log_file=str(log_path),
            max_file_size=512,
            backup_count=3,
        )
    )
    # Each log line is well over a few hundred bytes once the formatter is
    # applied; write enough to roll past 512 bytes.
    for i in range(50):
        obs.log_info(f"padding line {i} " + ("x" * 50))
    # Flush + close so RotatingFileHandler finalises the rollover.
    for handler in obs.logger.handlers:
        handler.close()
    backup = tmp_path / "rotate.log.1"
    assert backup.exists()


# --- create_child_observer / ContextualLoggingObserver ---


def test_create_child_observer_returns_contextual_observer():
    parent = _observer()
    child = parent.create_child_observer({"transaction_id": "abc"})
    assert isinstance(child, ContextualLoggingObserver)
    assert child.parent is parent
    assert child.context == {"transaction_id": "abc"}


def test_child_log_request_merges_context(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    parent = _observer()
    child = parent.create_child_observer({"transaction_id": "abc"})
    child.log_request("POST", "https://example.test/x")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert "abc" in rec.message


def test_child_log_response_merges_context(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    parent = _observer()
    child = parent.create_child_observer({"transaction_id": "abc"})
    child.log_response(200)
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert "abc" in rec.message


def test_child_log_exception_merges_context(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    parent = _observer()
    child = parent.create_child_observer({"transaction_id": "abc"})
    child.log_exception(ValueError("nope"), context={"step": "x"})
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    # Parent context flows into the `context` dict for log_exception.
    assert "abc" in rec.message
    assert "step" in rec.message


def test_child_log_exception_without_extra_context_still_includes_parent_context(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    parent = _observer()
    child = parent.create_child_observer({"transaction_id": "abc"})
    child.log_exception(ValueError("nope"))
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert "abc" in rec.message


def test_child_log_payment_operation_merges_context(caplog):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    parent = _observer()
    child = parent.create_child_observer({"transaction_id": "abc"})
    child.log_payment_operation("execute", "ideal", amount=10, currency="EUR")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert "abc" in rec.message
    assert "execute" in rec.message
    assert "ideal" in rec.message


@pytest.mark.parametrize(
    "method,expected_level",
    [
        ("log_info", logging.INFO),
        ("log_debug", logging.DEBUG),
        ("log_warning", logging.WARNING),
        ("log_error", logging.ERROR),
    ],
)
def test_child_log_info_family_merges_context(caplog, method, expected_level):
    caplog.set_level(logging.DEBUG, logger="buckaroo_sdk")
    parent = BuckarooLoggingObserver(
        LogConfig(level=LogLevel.DEBUG, destination=LogDestination.STDOUT)
    )
    child = parent.create_child_observer({"transaction_id": "abc"})
    getattr(child, method)("hello")
    rec = [r for r in caplog.records if r.name == "buckaroo_sdk"][0]
    assert rec.levelno == expected_level
    assert "abc" in rec.message
    assert "hello" in rec.message
