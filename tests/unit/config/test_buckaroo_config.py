"""Tests for buckaroo.config.buckaroo_config."""

import pytest

from buckaroo.config.buckaroo_config import (
    ApiVersion,
    BuckarooConfig,
    ConfigBuilder,
    DefaultConfig,
    Environment,
    ProductionConfig,
    TestConfig as _TestConfig,
    create_config_from_mode,
    create_production_config,
    create_test_config,
)


# --- Enums ---


def test_environment_values():
    assert Environment.TEST.value == "test"
    assert Environment.LIVE.value == "live"
    assert Environment("test") is Environment.TEST
    assert Environment("live") is Environment.LIVE


def test_api_version_values():
    assert ApiVersion.V1.value == "v1"
    assert ApiVersion.V2.value == "v2"


# --- BuckarooConfig defaults & validation ---


def test_defaults():
    cfg = BuckarooConfig()
    assert cfg.environment is Environment.TEST
    assert cfg.api_version is ApiVersion.V1
    assert cfg.timeout == 30
    assert cfg.retry_attempts == 3
    assert cfg.retry_delay == 1.0
    assert cfg.logging_enabled is True
    assert cfg.verify_ssl is True
    assert cfg.custom_endpoint is None
    assert cfg.user_agent == "BuckarooSDK-Python/1.0.0"
    assert cfg.max_redirects == 5


@pytest.mark.parametrize(
    "kwargs,msg",
    [
        ({"timeout": 0}, "Timeout must be greater than 0"),
        ({"timeout": -1}, "Timeout must be greater than 0"),
        ({"retry_attempts": -1}, "Retry attempts must be 0 or greater"),
        ({"retry_delay": -0.1}, "Retry delay must be 0 or greater"),
        ({"max_redirects": -1}, "Max redirects must be 0 or greater"),
    ],
)
def test_validation_errors(kwargs, msg):
    with pytest.raises(ValueError, match=msg):
        BuckarooConfig(**kwargs)


# --- api_endpoint ---


@pytest.mark.parametrize(
    "env,host",
    [
        (Environment.TEST, "testcheckout.buckaroo.nl"),
        (Environment.LIVE, "checkout.buckaroo.nl"),
    ],
)
def test_api_endpoint_switches_on_environment(env, host):
    cfg = BuckarooConfig(environment=env)
    assert cfg.api_endpoint.startswith("https://")
    assert host in cfg.api_endpoint


def test_custom_endpoint_overrides():
    cfg = BuckarooConfig(custom_endpoint="https://example.test")
    assert cfg.api_endpoint == "https://example.test"


def test_is_test_and_is_live_flags():
    t = BuckarooConfig(environment=Environment.TEST)
    assert t.is_test_environment is True
    assert t.is_live_environment is False
    live = BuckarooConfig(environment=Environment.LIVE)
    assert live.is_test_environment is False
    assert live.is_live_environment is True


# --- Headers ---


def test_get_request_headers_keys_and_values():
    cfg = BuckarooConfig(user_agent="UA/1")
    headers = cfg.get_request_headers()
    assert headers == {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "UA/1",
    }


# --- to_dict / from_dict ---


def test_to_dict_contains_documented_keys():
    cfg = BuckarooConfig()
    d = cfg.to_dict()
    for key in (
        "environment",
        "api_version",
        "api_endpoint",
        "timeout",
        "retry_attempts",
        "retry_delay",
        "logging_enabled",
        "verify_ssl",
        "custom_endpoint",
        "user_agent",
        "max_redirects",
        "is_test",
        "is_live",
    ):
        assert key in d


def test_from_dict_round_trip_preserves_fields():
    original = BuckarooConfig(
        environment=Environment.LIVE,
        api_version=ApiVersion.V2,
        timeout=45,
        retry_attempts=7,
        retry_delay=2.5,
        logging_enabled=False,
        verify_ssl=False,
        custom_endpoint="https://x.test",
        user_agent="UA/9",
        max_redirects=9,
    )
    restored = BuckarooConfig.from_dict(original.to_dict())
    assert restored.environment is Environment.LIVE
    assert restored.api_version is ApiVersion.V2
    assert restored.timeout == 45
    assert restored.retry_attempts == 7
    assert restored.retry_delay == 2.5
    assert restored.logging_enabled is False
    assert restored.verify_ssl is False
    assert restored.custom_endpoint == "https://x.test"
    assert restored.user_agent == "UA/9"
    assert restored.max_redirects == 9


def test_from_dict_accepts_enum_instances_and_ignores_extras():
    cfg = BuckarooConfig.from_dict(
        {
            "environment": Environment.LIVE,
            "api_version": ApiVersion.V2,
            "timeout": 12,
            "bogus_key": "ignored",
        }
    )
    assert cfg.environment is Environment.LIVE
    assert cfg.api_version is ApiVersion.V2
    assert cfg.timeout == 12


def test_copy_applies_changes():
    cfg = BuckarooConfig()
    copied = cfg.copy(timeout=99, environment=Environment.LIVE)
    assert copied.timeout == 99
    assert copied.environment is Environment.LIVE
    # original untouched
    assert cfg.timeout == 30
    assert cfg.environment is Environment.TEST


# --- Presets ---


def test_default_config_matches_base_defaults():
    d = DefaultConfig()
    assert d.environment is Environment.TEST
    assert d.timeout == 30
    assert d.retry_attempts == 3


def test_test_config_preset():
    t = _TestConfig()
    assert t.environment is Environment.TEST
    assert t.timeout == 10
    assert t.retry_attempts == 1
    assert t.retry_delay == 0.5
    assert t.logging_enabled is False


def test_production_config_preset():
    p = ProductionConfig()
    assert p.environment is Environment.LIVE
    assert p.timeout == 60
    assert p.retry_attempts == 5
    assert p.retry_delay == 2.0
    assert p.logging_enabled is True
    assert p.verify_ssl is True


# --- ConfigBuilder ---


def test_config_builder_fluent_chain():
    cfg = (
        ConfigBuilder()
        .environment(Environment.LIVE)
        .api_version(ApiVersion.V2)
        .timeout(45)
        .retry_attempts(4)
        .retry_delay(1.5)
        .enable_logging()
        .enable_ssl_verification()
        .custom_endpoint("https://custom.test")
        .user_agent("Agent/2")
        .max_redirects(7)
        .build()
    )
    assert cfg.environment is Environment.LIVE
    assert cfg.api_version is ApiVersion.V2
    assert cfg.timeout == 45
    assert cfg.retry_attempts == 4
    assert cfg.retry_delay == 1.5
    assert cfg.logging_enabled is True
    assert cfg.verify_ssl is True
    assert cfg.custom_endpoint == "https://custom.test"
    assert cfg.user_agent == "Agent/2"
    assert cfg.max_redirects == 7


def test_config_builder_test_environment_shortcut():
    cfg = ConfigBuilder().test_environment().build()
    assert cfg.environment is Environment.TEST


def test_config_builder_live_environment_shortcut():
    cfg = ConfigBuilder().live_environment().build()
    assert cfg.environment is Environment.LIVE


def test_config_builder_disable_toggles():
    cfg = ConfigBuilder().disable_logging().disable_ssl_verification().build()
    assert cfg.logging_enabled is False
    assert cfg.verify_ssl is False


def test_config_builder_empty_build_yields_defaults():
    cfg = ConfigBuilder().build()
    assert cfg.environment is Environment.TEST
    assert cfg.timeout == 30


# --- Mode helpers ---


def test_create_test_config_no_kwargs():
    cfg = create_test_config()
    assert cfg.environment is Environment.TEST
    assert cfg.timeout == 10


def test_create_production_config_no_kwargs():
    cfg = create_production_config()
    assert cfg.environment is Environment.LIVE
    assert cfg.timeout == 60


def test_create_test_config_with_kwargs_overrides_preset():
    cfg = create_test_config(timeout=25, retry_attempts=4)
    assert isinstance(cfg, BuckarooConfig)
    assert cfg.environment is Environment.TEST
    assert cfg.timeout == 25
    assert cfg.retry_attempts == 4
    # Preset values not overridden remain intact.
    assert cfg.retry_delay == 0.5
    assert cfg.logging_enabled is False


def test_create_production_config_with_kwargs_overrides_preset():
    cfg = create_production_config(timeout=120, retry_attempts=2)
    assert isinstance(cfg, BuckarooConfig)
    assert cfg.environment is Environment.LIVE
    assert cfg.timeout == 120
    assert cfg.retry_attempts == 2
    assert cfg.retry_delay == 2.0
    assert cfg.verify_ssl is True


def test_test_config_accepts_overrides_directly():
    t = _TestConfig(timeout=15, retry_attempts=2)
    assert t.environment is Environment.TEST
    assert t.timeout == 15
    assert t.retry_attempts == 2


def test_production_config_accepts_overrides_directly():
    p = ProductionConfig(timeout=90)
    assert p.environment is Environment.LIVE
    assert p.timeout == 90


def test_test_config_environment_is_locked():
    # Even if a caller tries to override the environment, presets stay locked.
    t = _TestConfig(environment=Environment.LIVE)
    assert t.environment is Environment.TEST


def test_production_config_environment_is_locked():
    p = ProductionConfig(environment=Environment.TEST)
    assert p.environment is Environment.LIVE


@pytest.mark.parametrize(
    "mode,expected_env,host",
    [
        ("test", Environment.TEST, "testcheckout.buckaroo.nl"),
        ("TEST", Environment.TEST, "testcheckout.buckaroo.nl"),
        ("live", Environment.LIVE, "checkout.buckaroo.nl"),
        ("LIVE", Environment.LIVE, "checkout.buckaroo.nl"),
    ],
)
def test_create_config_from_mode_valid(mode, expected_env, host):
    cfg = create_config_from_mode(mode)
    assert cfg.environment is expected_env
    assert host in cfg.api_endpoint


def test_create_config_from_mode_invalid_raises():
    with pytest.raises(ValueError, match="Invalid mode"):
        create_config_from_mode("invalid")
