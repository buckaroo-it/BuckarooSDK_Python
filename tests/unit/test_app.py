"""Tests for buckaroo.app.

Covers `buckaroo/app.py` at 100%. The module intentionally redefines
`BuckarooConfig` as a dataclass, shadowing `config.buckaroo_config.BuckarooConfig`.
This is documented in CLAUDE.md; a guardrail test pins the shadow so it cannot
silently drift.
"""

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.app import Buckaroo, BuckarooConfig
from buckaroo.config.buckaroo_config import BuckarooConfig as SdkBuckarooConfig
from buckaroo.config.buckaroo_config import Environment
from buckaroo.exceptions._authentication_error import AuthenticationError
from buckaroo.observers import BuckarooLoggingObserver, LogDestination, LogLevel
from buckaroo.observers.logging_observer import ContextualLoggingObserver
from buckaroo.services.payment_service import PaymentService
from buckaroo.services.solution_service import SolutionService


# --- Name-shadow guardrail ---

def test_app_buckarooconfig_is_not_sdk_buckarooconfig():
    assert BuckarooConfig is not SdkBuckarooConfig


# --- Construction & service exposure ---

def test_construct_with_config_exposes_payment_and_solution_services():
    app = Buckaroo(BuckarooConfig(store_key="sk", secret_key="ss"))

    assert isinstance(app.payments, PaymentService)
    assert isinstance(app.solutions, SolutionService)


def test_construct_initialises_logger_by_default():
    app = Buckaroo(BuckarooConfig(store_key="sk", secret_key="ss"))

    assert isinstance(app.logger, BuckarooLoggingObserver)
    assert app.get_logger() is app.logger


def test_enable_logging_false_skips_logger():
    app = Buckaroo(
        BuckarooConfig(store_key="sk", secret_key="ss", enable_logging=False)
    )

    assert app.logger is None
    assert app.get_logger() is None


# --- Env-var driven construction ---

def test_default_constructor_reads_store_and_secret_from_env(monkeypatch):
    monkeypatch.setenv("BUCKAROO_STORE_KEY", "env_store")
    monkeypatch.setenv("BUCKAROO_SECRET_KEY", "env_secret")

    app = Buckaroo()

    assert app.config.store_key == "env_store"
    assert app.config.secret_key == "env_secret"


def test_from_env_classmethod_returns_buckaroo_instance(monkeypatch):
    monkeypatch.setenv("BUCKAROO_STORE_KEY", "env_store")
    monkeypatch.setenv("BUCKAROO_SECRET_KEY", "env_secret")

    app = Buckaroo.from_env()

    assert isinstance(app, Buckaroo)
    assert app.config.store_key == "env_store"
    assert app.config.secret_key == "env_secret"


def test_missing_credentials_raises_authentication_error():
    with pytest.raises(AuthenticationError):
        Buckaroo()


# --- Mode handling ---

@pytest.mark.parametrize(
    "env_mode,expected_mode,expected_env",
    [
        ("test", "test", Environment.TEST),
        ("live", "live", Environment.LIVE),
        ("LIVE", "LIVE", Environment.LIVE),
    ],
)
def test_mode_env_maps_to_environment(env_credentials, env_mode, expected_mode, expected_env):
    env_credentials.setenv("BUCKAROO_MODE", env_mode)

    app = Buckaroo()

    assert app.config.mode == expected_mode
    assert app.client.config.environment is expected_env


def test_mode_test_via_config_arg():
    app = Buckaroo(BuckarooConfig(store_key="sk", secret_key="ss", mode="test"))

    assert app.config.mode == "test"
    assert app.client.config.environment is Environment.TEST


def test_invalid_mode_raises_value_error(env_credentials):
    env_credentials.setenv("BUCKAROO_MODE", "invalid")

    with pytest.raises(ValueError):
        Buckaroo()


# --- Timeout & retry settings ---

def test_timeout_and_retry_attempts_land_on_app_config():
    app = Buckaroo(
        BuckarooConfig(
            store_key="sk", secret_key="ss", timeout=45, retry_attempts=7
        )
    )

    assert app.config.timeout == 45
    assert app.config.retry_attempts == 7


def test_timeout_env_string_converted_to_int(env_credentials):
    env_credentials.setenv("BUCKAROO_TIMEOUT", "20")

    app = Buckaroo()

    assert app.config.timeout == 20
    assert isinstance(app.config.timeout, int)


def test_retry_attempts_env_string_converted_to_int(env_credentials):
    env_credentials.setenv("BUCKAROO_RETRY_ATTEMPTS", "5")

    app = Buckaroo()

    assert app.config.retry_attempts == 5
    assert isinstance(app.config.retry_attempts, int)


# --- Logging configuration ---

@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("DEBUG", LogLevel.DEBUG),
        ("info", LogLevel.INFO),
        ("WARNING", LogLevel.WARNING),
        ("ERROR", LogLevel.ERROR),
        ("CRITICAL", LogLevel.CRITICAL),
    ],
)
def test_log_level_env_maps_to_enum(env_credentials, env_value, expected):
    env_credentials.setenv("BUCKAROO_LOG_LEVEL", env_value)

    app = Buckaroo()

    assert app.config.log_level is expected


def test_invalid_log_level_falls_back_to_info(env_credentials):
    env_credentials.setenv("BUCKAROO_LOG_LEVEL", "bogus")

    app = Buckaroo()

    assert app.config.log_level is LogLevel.INFO


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("stdout", LogDestination.STDOUT),
        ("FILE", LogDestination.FILE),
        ("both", LogDestination.BOTH),
    ],
)
def test_log_destination_env_maps_to_enum(env_credentials, tmp_path, env_value, expected):
    env_credentials.setenv("BUCKAROO_LOG_DESTINATION", env_value)
    if expected in (LogDestination.FILE, LogDestination.BOTH):
        env_credentials.setenv("BUCKAROO_LOG_FILE", str(tmp_path / "app.log"))

    app = Buckaroo()

    assert app.config.log_destination is expected


def test_invalid_log_destination_falls_back_to_stdout(env_credentials):
    env_credentials.setenv("BUCKAROO_LOG_DESTINATION", "nowhere")

    app = Buckaroo()

    assert app.config.log_destination is LogDestination.STDOUT


def test_log_file_env_is_used_as_file_path(env_credentials, tmp_path):
    log_path = tmp_path / "custom.log"
    env_credentials.setenv("BUCKAROO_LOG_DESTINATION", "file")
    env_credentials.setenv("BUCKAROO_LOG_FILE", str(log_path))

    app = Buckaroo()
    app.log_info("probe_file_message")

    assert app.config.log_file == str(log_path)
    assert "probe_file_message" in log_path.read_text()


def test_log_destination_both_writes_to_file_and_stdout(
    env_credentials, tmp_path, capsys
):
    log_path = tmp_path / "both.log"
    env_credentials.setenv("BUCKAROO_LOG_DESTINATION", "both")
    env_credentials.setenv("BUCKAROO_LOG_FILE", str(log_path))

    app = Buckaroo()
    app.log_info("probe_both_message")

    file_content = log_path.read_text()
    captured = capsys.readouterr()

    assert "probe_both_message" in file_content
    assert "probe_both_message" in captured.out


def test_mask_sensitive_env_false(env_credentials):
    env_credentials.setenv("BUCKAROO_LOG_MASK_SENSITIVE", "false")

    app = Buckaroo()

    assert app.config.mask_sensitive_data is False


def test_mask_sensitive_env_true_default(env_credentials):
    app = Buckaroo()

    assert app.config.mask_sensitive_data is True


# --- quick_setup classmethod ---

def test_quick_setup_returns_buckaroo_instance():
    app = Buckaroo.quick_setup(store_key="sk", secret_key="ss")

    assert isinstance(app, Buckaroo)
    assert app.config.store_key == "sk"
    assert app.config.secret_key == "ss"
    assert app.config.mode == "test"
    assert app.config.log_destination is LogDestination.STDOUT


def test_quick_setup_with_live_mode_and_file_logging(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    app = Buckaroo.quick_setup(
        store_key="sk", secret_key="ss", mode="live", log_to_stdout=False
    )

    assert app.config.mode == "live"
    assert app.config.log_destination is LogDestination.FILE
    assert app.client.config.environment is Environment.LIVE


# --- Log helper methods ---

def test_log_helpers_write_via_logger(env_credentials, tmp_path):
    log_path = tmp_path / "helpers.log"
    env_credentials.setenv("BUCKAROO_LOG_LEVEL", "DEBUG")
    env_credentials.setenv("BUCKAROO_LOG_DESTINATION", "file")
    env_credentials.setenv("BUCKAROO_LOG_FILE", str(log_path))

    app = Buckaroo()
    app.log_debug("debug_msg")
    app.log_info("info_msg")
    app.log_warning("warn_msg")
    app.log_error("error_msg")
    app.log_exception(RuntimeError("boom"))

    contents = log_path.read_text()
    assert "debug_msg" in contents
    assert "info_msg" in contents
    assert "warn_msg" in contents
    assert "error_msg" in contents
    assert "boom" in contents


def test_log_helpers_no_op_when_logging_disabled():
    app = Buckaroo(
        BuckarooConfig(store_key="sk", secret_key="ss", enable_logging=False)
    )

    # All helpers must be safe no-ops when logger is None.
    app.log_debug("x")
    app.log_info("x")
    app.log_warning("x")
    app.log_error("x")
    app.log_exception(RuntimeError("x"))

    assert app.logger is None


# --- Accessors ---

def test_get_client_returns_underlying_client():
    app = Buckaroo(BuckarooConfig(store_key="sk", secret_key="ss"))

    client = app.get_client()

    assert isinstance(client, BuckarooClient)
    assert client is app.client


def test_get_client_raises_when_client_not_initialised():
    app = Buckaroo(BuckarooConfig(store_key="sk", secret_key="ss"))
    app.client = None

    with pytest.raises(RuntimeError, match="Client not initialized"):
        app.get_client()


def test_create_child_logger_returns_child_observer():
    app = Buckaroo(BuckarooConfig(store_key="sk", secret_key="ss"))

    child = app.create_child_logger({"request_id": "abc"})

    assert isinstance(child, ContextualLoggingObserver)


def test_create_child_logger_returns_none_when_logging_disabled():
    app = Buckaroo(
        BuckarooConfig(store_key="sk", secret_key="ss", enable_logging=False)
    )

    assert app.create_child_logger({"request_id": "abc"}) is None


# --- Context manager ---

def test_context_manager_exposes_app_inside_block():
    with Buckaroo(BuckarooConfig(store_key="sk", secret_key="ss")) as app:
        assert isinstance(app, Buckaroo)
        assert isinstance(app.payments, PaymentService)


def test_context_manager_logs_exception_on_failure_path(env_credentials, tmp_path):
    log_path = tmp_path / "ctx.log"
    env_credentials.setenv("BUCKAROO_LOG_LEVEL", "DEBUG")
    env_credentials.setenv("BUCKAROO_LOG_DESTINATION", "file")
    env_credentials.setenv("BUCKAROO_LOG_FILE", str(log_path))

    with pytest.raises(RuntimeError, match="ctx_boom"):
        with Buckaroo() as app:
            assert app is not None
            raise RuntimeError("ctx_boom")

    assert "ctx_boom" in log_path.read_text()


def test_context_manager_works_when_logging_disabled():
    app = Buckaroo(
        BuckarooConfig(store_key="sk", secret_key="ss", enable_logging=False)
    )

    with app as ctx:
        assert ctx is app


def test_context_manager_propagates_exception_when_logging_disabled():
    app = Buckaroo(
        BuckarooConfig(store_key="sk", secret_key="ss", enable_logging=False)
    )

    with pytest.raises(RuntimeError, match="no_logger_boom"):
        with app:
            raise RuntimeError("no_logger_boom")


# --- Edge-case branches ---

def test_missing_credentials_with_logging_disabled_still_raises():
    with pytest.raises(AuthenticationError):
        Buckaroo(BuckarooConfig(enable_logging=False))


def test_client_setup_exception_is_logged_and_reraised(env_credentials, tmp_path):
    log_path = tmp_path / "setup.log"
    env_credentials.setenv("BUCKAROO_LOG_DESTINATION", "file")
    env_credentials.setenv("BUCKAROO_LOG_FILE", str(log_path))

    def _boom(*args, **kwargs):
        raise RuntimeError("client_boom")

    env_credentials.setattr("buckaroo.app.BuckarooClient", _boom)

    with pytest.raises(RuntimeError, match="client_boom"):
        Buckaroo()

    assert "client_boom" in log_path.read_text()


def test_client_setup_exception_reraises_without_logger(env_credentials):
    """The exception propagates when enable_logging=False (logger is None)."""
    def _boom(*args, **kwargs):
        raise RuntimeError("silent_boom")

    env_credentials.setattr("buckaroo.app.BuckarooClient", _boom)

    config = BuckarooConfig(store_key="sk", secret_key="ss", enable_logging=False)
    assert config.enable_logging is False

    with pytest.raises(RuntimeError, match="silent_boom"):
        app = Buckaroo(config)

    # Verify we actually took the logger-is-None branch: the Buckaroo
    # constructor sets self.logger before _setup_client, so we can't inspect
    # a half-constructed instance. Instead we confirm the config disables
    # logging, which causes _setup_logging to skip logger creation.
