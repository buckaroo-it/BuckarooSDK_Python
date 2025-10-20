
from typing import Optional, Union
from .exceptions._authentication_error import AuthenticationError
from .config.buckaroo_config import BuckarooConfig, create_config_from_mode
from .http.client import BuckarooHttpClient


class BuckarooClient(object):
    """
    Buckaroo Payment Gateway Client.
    
    This is the main client class for interacting with the Buckaroo payment gateway.
    It provides access to payment services and manages authentication and configuration.
    
    Args:
        store_key (str): Your Buckaroo store key.
        secret_key (str): Your Buckaroo secret key.
        mode (str, optional): Environment mode ('test' or 'live'). Defaults to 'test'.
            This parameter is deprecated, use config parameter instead.
        config (BuckarooConfig, optional): Configuration object. If not provided,
            a default configuration will be created based on the mode parameter.
        http_strategy (str, optional): HTTP strategy to use ('requests' or 'curl').
            If not provided, will auto-select the best available strategy.
    
    Example:
        Basic usage with mode:
        >>> client = BuckarooClient("store_key", "secret_key", mode="test")
        
        Advanced usage with configuration:
        >>> from buckaroo.config.buckaroo_config import BuckarooConfig, Environment
        >>> config = BuckarooConfig(environment=Environment.LIVE, timeout=60)
        >>> client = BuckarooClient("store_key", "secret_key", config=config)
        
        Usage with specific HTTP strategy:
        >>> client = BuckarooClient("store_key", "secret_key", http_strategy="curl")
    """

    def __init__(
        self, 
        store_key: str, 
        secret_key: str, 
        mode: str = "test",
        config: Optional[BuckarooConfig] = None,
        http_strategy: Optional[str] = None
    ) -> None:
        """
        Initialize the Buckaroo Client class.
        
        Args:
            store_key (str): Your Buckaroo store key
            secret_key (str): Your Buckaroo secret key  
            mode (str): Environment mode ('test' or 'live'). Deprecated, use config instead
            config (BuckarooConfig, optional): Configuration object
            http_strategy (str, optional): HTTP strategy to use ('requests' or 'curl')
                                         If None, will auto-select best available strategy
        """

        if store_key is None or not store_key.strip():
            raise AuthenticationError("Store key must be provided")
        
        if secret_key is None or not secret_key.strip():
            raise AuthenticationError("Secret key must be provided")
        
        self.store_key = store_key.strip()
        self.secret_key = secret_key.strip()
        self.http_strategy = http_strategy
        
        # Handle configuration
        if config is not None:
            self.config = config
        else:
            # Create config from mode for backward compatibility
            self.config = create_config_from_mode(mode)
        
        # Initialize HTTP client with strategy
        self.http_client = BuckarooHttpClient(
            self.store_key, 
            self.secret_key, 
            self.config, 
            self.http_strategy
        )
    
    @property
    def is_test_environment(self) -> bool:
        """
        Check if client is configured for test environment.
        
        Returns:
            bool: True if in test environment, False if live.
        """
        return self.config.is_test_environment
    
    @property
    def is_live_environment(self) -> bool:
        """
        Check if client is configured for live environment.
        
        Returns:
            bool: True if in live environment, False if test.
        """
        return self.config.is_live_environment
    
    @property
    def api_endpoint(self) -> str:
        """
        Get the API endpoint URL.
        
        Returns:
            str: The API endpoint URL.
        """
        return self.config.api_endpoint
    
    def get_config_info(self) -> dict:
        """
        Get configuration information.
        
        Returns:
            dict: Configuration information (safe for logging).
        """
        return {
            "environment": self.config.environment.value,
            "api_endpoint": self.config.api_endpoint,
            "timeout": self.config.timeout,
            "retry_attempts": self.config.retry_attempts,
            "api_version": self.config.api_version.value,
            "logging_enabled": self.config.logging_enabled,
        }
