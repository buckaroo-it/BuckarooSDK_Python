import unittest
from buckaroo.config.buckaroo_config import (
    BuckarooConfig, Environment, ApiVersion, DefaultConfig, TestConfig, 
    ProductionConfig, ConfigBuilder, create_test_config, create_production_config,
    create_config_from_mode
)


class TestBuckarooConfig(unittest.TestCase):
    """Test suite for BuckarooConfig."""

    def test_default_config_creation(self):
        """Test creating a default configuration."""
        config = BuckarooConfig()
        
        self.assertEqual(config.environment, Environment.TEST)
        self.assertEqual(config.api_version, ApiVersion.V1)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.retry_attempts, 3)
        self.assertEqual(config.retry_delay, 1.0)
        self.assertTrue(config.logging_enabled)
        self.assertTrue(config.verify_ssl)
        self.assertIsNone(config.custom_endpoint)
        self.assertEqual(config.user_agent, "BuckarooSDK-Python/1.0.0")
        self.assertEqual(config.max_redirects, 5)

    def test_custom_config_creation(self):
        """Test creating a custom configuration."""
        config = BuckarooConfig(
            environment=Environment.LIVE,
            timeout=60,
            retry_attempts=5,
            logging_enabled=False
        )
        
        self.assertEqual(config.environment, Environment.LIVE)
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.retry_attempts, 5)
        self.assertFalse(config.logging_enabled)

    def test_api_endpoint_test_environment(self):
        """Test API endpoint for test environment."""
        config = BuckarooConfig(environment=Environment.TEST)
        self.assertEqual(config.api_endpoint, "https://testcheckout.buckaroo.nl")

    def test_api_endpoint_live_environment(self):
        """Test API endpoint for live environment."""
        config = BuckarooConfig(environment=Environment.LIVE)
        self.assertEqual(config.api_endpoint, "https://checkout.buckaroo.nl")

    def test_custom_endpoint(self):
        """Test custom API endpoint."""
        custom_url = "https://custom.api.example.com"
        config = BuckarooConfig(custom_endpoint=custom_url)
        self.assertEqual(config.api_endpoint, custom_url)

    def test_is_test_environment(self):
        """Test environment detection methods."""
        test_config = BuckarooConfig(environment=Environment.TEST)
        live_config = BuckarooConfig(environment=Environment.LIVE)
        
        self.assertTrue(test_config.is_test_environment)
        self.assertFalse(test_config.is_live_environment)
        
        self.assertFalse(live_config.is_test_environment)
        self.assertTrue(live_config.is_live_environment)

    def test_get_request_headers(self):
        """Test request headers generation."""
        config = BuckarooConfig(user_agent="Custom-Agent/1.0")
        headers = config.get_request_headers()
        
        expected_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Custom-Agent/1.0",
        }
        
        self.assertEqual(headers, expected_headers)

    def test_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = BuckarooConfig(
            environment=Environment.LIVE,
            timeout=45,
            retry_attempts=2
        )
        
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict["environment"], "live")
        self.assertEqual(config_dict["api_version"], "v1")
        self.assertEqual(config_dict["timeout"], 45)
        self.assertEqual(config_dict["retry_attempts"], 2)
        self.assertTrue(config_dict["is_live"])
        self.assertFalse(config_dict["is_test"])

    def test_from_dict(self):
        """Test configuration from dictionary creation."""
        config_dict = {
            "environment": "live",
            "api_version": "v2",
            "timeout": 90,
            "retry_attempts": 4,
            "logging_enabled": False
        }
        
        config = BuckarooConfig.from_dict(config_dict)
        
        self.assertEqual(config.environment, Environment.LIVE)
        self.assertEqual(config.api_version, ApiVersion.V2)
        self.assertEqual(config.timeout, 90)
        self.assertEqual(config.retry_attempts, 4)
        self.assertFalse(config.logging_enabled)

    def test_copy_config(self):
        """Test configuration copying with changes."""
        original = BuckarooConfig(timeout=30, retry_attempts=3)
        copied = original.copy(timeout=60, environment=Environment.LIVE)
        
        # Original should be unchanged
        self.assertEqual(original.timeout, 30)
        self.assertEqual(original.environment, Environment.TEST)
        
        # Copy should have changes
        self.assertEqual(copied.timeout, 60)
        self.assertEqual(copied.environment, Environment.LIVE)
        self.assertEqual(copied.retry_attempts, 3)  # Unchanged value

    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid timeout
        with self.assertRaises(ValueError):
            BuckarooConfig(timeout=-1)
        
        # Test invalid retry attempts
        with self.assertRaises(ValueError):
            BuckarooConfig(retry_attempts=-1)
        
        # Test invalid retry delay
        with self.assertRaises(ValueError):
            BuckarooConfig(retry_delay=-1.0)
        
        # Test invalid max redirects
        with self.assertRaises(ValueError):
            BuckarooConfig(max_redirects=-1)


class TestConfigClasses(unittest.TestCase):
    """Test suite for specialized config classes."""

    def test_default_config(self):
        """Test DefaultConfig class."""
        config = DefaultConfig()
        self.assertEqual(config.environment, Environment.TEST)
        self.assertEqual(config.timeout, 30)

    def test_test_config(self):
        """Test TestConfig class."""
        config = TestConfig()
        self.assertEqual(config.environment, Environment.TEST)
        self.assertEqual(config.timeout, 10)
        self.assertEqual(config.retry_attempts, 1)
        self.assertFalse(config.logging_enabled)

    def test_production_config(self):
        """Test ProductionConfig class."""
        config = ProductionConfig()
        self.assertEqual(config.environment, Environment.LIVE)
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.retry_attempts, 5)
        self.assertTrue(config.logging_enabled)


class TestConfigBuilder(unittest.TestCase):
    """Test suite for ConfigBuilder."""

    def test_config_builder_fluent_interface(self):
        """Test ConfigBuilder fluent interface."""
        config = (ConfigBuilder()
                 .live_environment()
                 .timeout(45)
                 .retry_attempts(3)
                 .enable_logging()
                 .disable_ssl_verification()
                 .build())
        
        self.assertEqual(config.environment, Environment.LIVE)
        self.assertEqual(config.timeout, 45)
        self.assertEqual(config.retry_attempts, 3)
        self.assertTrue(config.logging_enabled)
        self.assertFalse(config.verify_ssl)

    def test_config_builder_shortcuts(self):
        """Test ConfigBuilder shortcut methods."""
        test_config = (ConfigBuilder()
                      .test_environment()
                      .build())
        
        live_config = (ConfigBuilder()
                      .live_environment()
                      .build())
        
        self.assertEqual(test_config.environment, Environment.TEST)
        self.assertEqual(live_config.environment, Environment.LIVE)

    def test_config_builder_custom_values(self):
        """Test ConfigBuilder with custom values."""
        config = (ConfigBuilder()
                 .custom_endpoint("https://custom.example.com")
                 .user_agent("MyApp/2.0")
                 .max_redirects(10)
                 .retry_delay(2.5)
                 .build())
        
        self.assertEqual(config.custom_endpoint, "https://custom.example.com")
        self.assertEqual(config.user_agent, "MyApp/2.0")
        self.assertEqual(config.max_redirects, 10)
        self.assertEqual(config.retry_delay, 2.5)


class TestConfigConvenienceFunctions(unittest.TestCase):
    """Test suite for convenience functions."""

    def test_create_test_config(self):
        """Test create_test_config function."""
        config = create_test_config()
        self.assertEqual(config.environment, Environment.TEST)
        self.assertEqual(config.timeout, 10)
        
        # Test with overrides
        config_with_overrides = create_test_config(timeout=20, retry_attempts=5)
        self.assertEqual(config_with_overrides.timeout, 20)
        self.assertEqual(config_with_overrides.retry_attempts, 5)
        self.assertEqual(config_with_overrides.environment, Environment.TEST)

    def test_create_production_config(self):
        """Test create_production_config function."""
        config = create_production_config()
        self.assertEqual(config.environment, Environment.LIVE)
        self.assertEqual(config.timeout, 60)
        
        # Test with overrides
        config_with_overrides = create_production_config(timeout=120)
        self.assertEqual(config_with_overrides.timeout, 120)
        self.assertEqual(config_with_overrides.environment, Environment.LIVE)

    def test_create_config_from_mode(self):
        """Test create_config_from_mode function."""
        test_config = create_config_from_mode("test")
        live_config = create_config_from_mode("live")
        
        self.assertEqual(test_config.environment, Environment.TEST)
        self.assertEqual(live_config.environment, Environment.LIVE)
        
        # Test case insensitive
        test_config_upper = create_config_from_mode("TEST")
        self.assertEqual(test_config_upper.environment, Environment.TEST)
        
        # Test invalid mode
        with self.assertRaises(ValueError):
            create_config_from_mode("invalid")


if __name__ == '__main__':
    unittest.main()