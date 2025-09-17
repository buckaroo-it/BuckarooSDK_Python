"""
Example: BuckarooConfig Usage

This example demonstrates how to use the BuckarooConfig system with the Buckaroo SDK
for different configuration scenarios.
"""

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.config.buckaroo_config import (
    BuckarooConfig, Environment, ApiVersion, ConfigBuilder,
    create_test_config, create_production_config
)


def main():
    print("=== BuckarooConfig Examples ===\n")
    
    # Example 1: Basic usage with mode (backward compatibility)
    print("1. Basic Usage (Backward Compatible):")
    
    client_test = BuckarooClient("test_store_key", "test_secret_key", mode="test")
    client_live = BuckarooClient("live_store_key", "live_secret_key", mode="live")
    
    print(f"   Test client endpoint: {client_test.api_endpoint}")
    print(f"   Live client endpoint: {client_live.api_endpoint}")
    print(f"   Test environment: {client_test.is_test_environment}")
    print(f"   Live environment: {client_live.is_live_environment}\n")
    
    # Example 2: Using BuckarooConfig directly
    print("2. Direct BuckarooConfig Usage:")
    
    config = BuckarooConfig(
        environment=Environment.LIVE,
        timeout=60,
        retry_attempts=5,
        logging_enabled=True
    )
    
    client = BuckarooClient("store_key", "secret_key", config=config)
    
    print(f"   Environment: {config.environment.value}")
    print(f"   API Endpoint: {config.api_endpoint}")
    print(f"   Timeout: {config.timeout}s")
    print(f"   Retry Attempts: {config.retry_attempts}")
    print(f"   Logging Enabled: {config.logging_enabled}\n")
    
    # Example 3: Using ConfigBuilder (fluent interface)
    print("3. ConfigBuilder (Fluent Interface):")
    
    builder_config = (ConfigBuilder()
                     .live_environment()
                     .timeout(45)
                     .retry_attempts(3)
                     .retry_delay(2.0)
                     .enable_logging()
                     .user_agent("MyApp-BuckarooSDK/1.0")
                     .build())
    
    client_builder = BuckarooClient("store_key", "secret_key", config=builder_config)
    
    print(f"   Built config: {builder_config.to_dict()}\n")
    
    # Example 4: Convenience functions
    print("4. Convenience Functions:")
    
    # Quick test configuration
    test_config = create_test_config(timeout=15, retry_attempts=2)
    test_client = BuckarooClient("test_key", "test_secret", config=test_config)
    
    # Quick production configuration
    prod_config = create_production_config(timeout=90)
    prod_client = BuckarooClient("prod_key", "prod_secret", config=prod_config)
    
    print(f"   Test config info: {test_client.get_config_info()}")
    print(f"   Prod config info: {prod_client.get_config_info()}\n")
    
    # Example 5: Custom endpoint configuration
    print("5. Custom Endpoint Configuration:")
    
    custom_config = BuckarooConfig(
        custom_endpoint="https://custom-api.mycompany.com",
        timeout=30,
        verify_ssl=False  # Only for development/testing
    )
    
    custom_client = BuckarooClient("store_key", "secret_key", config=custom_config)
    
    print(f"   Custom endpoint: {custom_config.api_endpoint}")
    print(f"   SSL verification: {custom_config.verify_ssl}\n")
    
    # Example 6: Configuration copying and modification
    print("6. Configuration Copying:")
    
    base_config = create_test_config()
    
    # Create variations of the base config
    fast_config = base_config.copy(timeout=5, retry_attempts=1)
    slow_config = base_config.copy(timeout=120, retry_attempts=10)
    
    print(f"   Base config timeout: {base_config.timeout}s")
    print(f"   Fast config timeout: {fast_config.timeout}s")
    print(f"   Slow config timeout: {slow_config.timeout}s\n")
    
    # Example 7: Configuration from dictionary
    print("7. Configuration from Dictionary:")
    
    config_dict = {
        "environment": "live",
        "api_version": "v1", 
        "timeout": 75,
        "retry_attempts": 4,
        "logging_enabled": True,
        "user_agent": "E-commerce-Platform/3.2.1"
    }
    
    dict_config = BuckarooConfig.from_dict(config_dict)
    dict_client = BuckarooClient("store_key", "secret_key", config=dict_config)
    
    print(f"   Config from dict: {dict_config.to_dict()}\n")
    
    # Example 8: Request headers
    print("8. Request Headers:")
    
    headers_config = BuckarooConfig(user_agent="MySpecialApp/2.0.0")
    headers = headers_config.get_request_headers()
    
    print(f"   Default headers: {headers}\n")
    
    # Example 9: Different API versions
    print("9. API Version Configuration:")
    
    v1_config = BuckarooConfig(api_version=ApiVersion.V1)
    v2_config = BuckarooConfig(api_version=ApiVersion.V2)
    
    print(f"   V1 Config: {v1_config.api_version.value}")
    print(f"   V2 Config: {v2_config.api_version.value}\n")
    
    # Example 10: Environment-specific configurations
    print("10. Environment-Specific Configurations:")
    
    # Development environment
    dev_config = (ConfigBuilder()
                 .test_environment()
                 .timeout(10)
                 .retry_attempts(1)
                 .disable_ssl_verification()
                 .enable_logging()
                 .build())
    
    # Staging environment  
    staging_config = (ConfigBuilder()
                     .test_environment()
                     .timeout(30)
                     .retry_attempts(3)
                     .enable_ssl_verification()
                     .enable_logging()
                     .build())
    
    # Production environment
    production_config = (ConfigBuilder()
                        .live_environment()
                        .timeout(60)
                        .retry_attempts(5)
                        .retry_delay(3.0)
                        .enable_ssl_verification()
                        .enable_logging()
                        .build())
    
    print(f"   Development: {dev_config.environment.value}, timeout: {dev_config.timeout}s")
    print(f"   Staging: {staging_config.environment.value}, timeout: {staging_config.timeout}s") 
    print(f"   Production: {production_config.environment.value}, timeout: {production_config.timeout}s\n")
    
    print("=== Configuration Best Practices ===")
    print("• Use create_test_config() for development and testing")
    print("• Use create_production_config() for live environments")
    print("• Configure timeouts based on your application's needs")
    print("• Enable logging in development, consider disabling in production")
    print("• Always verify SSL certificates in production")
    print("• Use custom user agents for better API tracking")
    print("• Set retry attempts based on your error tolerance")
    print("• Consider using environment variables for configuration")


if __name__ == "__main__":
    main()