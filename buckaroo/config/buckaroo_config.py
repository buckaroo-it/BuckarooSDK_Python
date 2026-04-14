"""
Buckaroo SDK Configuration Module.

This module provides configuration classes for the Buckaroo SDK, allowing
customization of API endpoints, timeouts, retry logic, and other settings.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Buckaroo API environment options."""
    TEST = "test"
    LIVE = "live"


class ApiVersion(Enum):
    """Supported Buckaroo API versions."""
    V1 = "v1"
    V2 = "v2"


@dataclass
class BuckarooConfig:
    """
    Configuration class for Buckaroo SDK.
    
    This class manages all configuration settings for the Buckaroo SDK,
    including API endpoints, timeouts, retry logic, and authentication settings.
    
    Attributes:
        environment (Environment): The API environment (test/live).
        api_version (ApiVersion): The API version to use.
        timeout (int): Request timeout in seconds.
        retry_attempts (int): Number of retry attempts for failed requests.
        retry_delay (float): Delay between retry attempts in seconds.
        logging_enabled (bool): Whether to enable SDK logging.
        verify_ssl (bool): Whether to verify SSL certificates.
        custom_endpoint (Optional[str]): Custom API endpoint URL.
        user_agent (str): User agent string for HTTP requests.
        max_redirects (int): Maximum number of HTTP redirects to follow.
        
    Example:
        >>> config = BuckarooConfig(
        ...     environment=Environment.LIVE,
        ...     timeout=60,
        ...     retry_attempts=5
        ... )
        >>> client = BuckarooClient("store_key", "secret_key", config=config)
    """
    
    environment: Environment = Environment.TEST
    api_version: ApiVersion = ApiVersion.V1
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    logging_enabled: bool = True
    verify_ssl: bool = True
    custom_endpoint: Optional[str] = None
    user_agent: str = "BuckarooSDK-Python/1.0.0"
    max_redirects: int = 5
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            ValueError: If configuration parameters are invalid.
        """
        if self.timeout <= 0:
            raise ValueError("Timeout must be greater than 0")
            
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts must be 0 or greater")
            
        if self.retry_delay < 0:
            raise ValueError("Retry delay must be 0 or greater")
            
        if self.max_redirects < 0:
            raise ValueError("Max redirects must be 0 or greater")
    
    @property
    def api_endpoint(self) -> str:
        """
        Get the API endpoint URL based on environment.
        
        Returns:
            str: The API endpoint URL.
        """
        if self.custom_endpoint:
            return self.custom_endpoint
            
        if self.environment == Environment.TEST:
            return "https://testcheckout.buckaroo.nl"
        else:  # LIVE
            return "https://checkout.buckaroo.nl"
    
    @property
    def is_test_environment(self) -> bool:
        """
        Check if currently in test environment.
        
        Returns:
            bool: True if in test environment, False if live.
        """
        return self.environment == Environment.TEST
    
    @property
    def is_live_environment(self) -> bool:
        """
        Check if currently in live environment.
        
        Returns:
            bool: True if in live environment, False if test.
        """
        return self.environment == Environment.LIVE
    
    def get_request_headers(self) -> Dict[str, str]:
        """
        Get default HTTP headers for API requests.
        
        Returns:
            Dict[str, str]: Dictionary of HTTP headers.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary.
        """
        return {
            "environment": self.environment.value,
            "api_version": self.api_version.value,
            "api_endpoint": self.api_endpoint,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "logging_enabled": self.logging_enabled,
            "verify_ssl": self.verify_ssl,
            "custom_endpoint": self.custom_endpoint,
            "user_agent": self.user_agent,
            "max_redirects": self.max_redirects,
            "is_test": self.is_test_environment,
            "is_live": self.is_live_environment,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BuckarooConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict (Dict[str, Any]): Configuration dictionary.
            
        Returns:
            BuckarooConfig: New configuration instance.
        """
        # Convert string values to enums
        if "environment" in config_dict:
            if isinstance(config_dict["environment"], str):
                config_dict["environment"] = Environment(config_dict["environment"])
                
        if "api_version" in config_dict:
            if isinstance(config_dict["api_version"], str):
                config_dict["api_version"] = ApiVersion(config_dict["api_version"])
        
        # Filter out extra keys
        valid_keys = {
            "environment", "api_version", "timeout", "retry_attempts",
            "retry_delay", "logging_enabled", "verify_ssl", "custom_endpoint",
            "user_agent", "max_redirects"
        }
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}
        
        return cls(**filtered_dict)
    
    def copy(self, **changes) -> 'BuckarooConfig':
        """
        Create a copy of the configuration with optional changes.
        
        Args:
            **changes: Configuration parameters to change.
            
        Returns:
            BuckarooConfig: New configuration instance with changes applied.
            
        Example:
            >>> new_config = config.copy(timeout=60, environment=Environment.LIVE)
        """
        config_dict = self.to_dict()
        config_dict.update(changes)
        return self.from_dict(config_dict)


class DefaultConfig(BuckarooConfig):
    """
    Default configuration for Buckaroo SDK.
    
    This class provides sensible defaults for most use cases.
    """
    pass


class TestConfig(BuckarooConfig):
    """Test preset: short timeouts, no logging. Environment locked to TEST."""

    def __init__(self, **overrides):
        defaults = dict(
            timeout=10,
            retry_attempts=1,
            retry_delay=0.5,
            logging_enabled=False,
        )
        defaults.update(overrides)
        defaults["environment"] = Environment.TEST
        super().__init__(**defaults)


class ProductionConfig(BuckarooConfig):
    """Production preset: conservative timeouts, logging on. Environment locked to LIVE."""

    def __init__(self, **overrides):
        defaults = dict(
            timeout=60,
            retry_attempts=5,
            retry_delay=2.0,
            logging_enabled=True,
            verify_ssl=True,
        )
        defaults.update(overrides)
        defaults["environment"] = Environment.LIVE
        super().__init__(**defaults)


class ConfigBuilder:
    """
    Builder class for creating Buckaroo configurations.
    
    This class provides a fluent interface for building configurations
    with method chaining.
    
    Example:
        >>> config = (ConfigBuilder()
        ...     .environment(Environment.LIVE)
        ...     .timeout(45)
        ...     .retry_attempts(3)
        ...     .enable_logging()
        ...     .build())
    """
    
    def __init__(self):
        self._config_dict = {}
    
    def environment(self, env: Environment) -> 'ConfigBuilder':
        """Set the environment."""
        self._config_dict["environment"] = env
        return self
    
    def test_environment(self) -> 'ConfigBuilder':
        """Set test environment."""
        return self.environment(Environment.TEST)
    
    def live_environment(self) -> 'ConfigBuilder':
        """Set live environment."""
        return self.environment(Environment.LIVE)
    
    def api_version(self, version: ApiVersion) -> 'ConfigBuilder':
        """Set the API version."""
        self._config_dict["api_version"] = version
        return self
    
    def timeout(self, seconds: int) -> 'ConfigBuilder':
        """Set request timeout."""
        self._config_dict["timeout"] = seconds
        return self
    
    def retry_attempts(self, attempts: int) -> 'ConfigBuilder':
        """Set retry attempts."""
        self._config_dict["retry_attempts"] = attempts
        return self
    
    def retry_delay(self, delay: float) -> 'ConfigBuilder':
        """Set retry delay."""
        self._config_dict["retry_delay"] = delay
        return self
    
    def enable_logging(self) -> 'ConfigBuilder':
        """Enable logging."""
        self._config_dict["logging_enabled"] = True
        return self
    
    def disable_logging(self) -> 'ConfigBuilder':
        """Disable logging."""
        self._config_dict["logging_enabled"] = False
        return self
    
    def enable_ssl_verification(self) -> 'ConfigBuilder':
        """Enable SSL verification."""
        self._config_dict["verify_ssl"] = True
        return self
    
    def disable_ssl_verification(self) -> 'ConfigBuilder':
        """Disable SSL verification (not recommended for production)."""
        self._config_dict["verify_ssl"] = False
        return self
    
    def custom_endpoint(self, endpoint: str) -> 'ConfigBuilder':
        """Set custom API endpoint."""
        self._config_dict["custom_endpoint"] = endpoint
        return self
    
    def user_agent(self, agent: str) -> 'ConfigBuilder':
        """Set custom user agent."""
        self._config_dict["user_agent"] = agent
        return self
    
    def max_redirects(self, redirects: int) -> 'ConfigBuilder':
        """Set maximum redirects."""
        self._config_dict["max_redirects"] = redirects
        return self
    
    def build(self) -> BuckarooConfig:
        """
        Build the configuration.
        
        Returns:
            BuckarooConfig: The built configuration.
        """
        return BuckarooConfig.from_dict(self._config_dict)


# Convenience functions for common configurations
def create_test_config(**kwargs) -> BuckarooConfig:
    """
    Create a test configuration with optional overrides.
    
    Args:
        **kwargs: Configuration overrides.
        
    Returns:
        BuckarooConfig: Test configuration.
    """
    config = TestConfig()
    if kwargs:
        return config.copy(**kwargs)
    return config


def create_production_config(**kwargs) -> BuckarooConfig:
    """
    Create a production configuration with optional overrides.
    
    Args:
        **kwargs: Configuration overrides.
        
    Returns:
        BuckarooConfig: Production configuration.
    """
    config = ProductionConfig()
    if kwargs:
        return config.copy(**kwargs)
    return config


def create_config_from_mode(mode: str) -> BuckarooConfig:
    """
    Create configuration from mode string (for backward compatibility).
    
    Args:
        mode (str): Mode string ("test" or "live").
        
    Returns:
        BuckarooConfig: Configuration for the specified mode.
    """
    if mode.lower() == "test":
        return create_test_config()
    elif mode.lower() == "live":
        return create_production_config()
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'test' or 'live'.")