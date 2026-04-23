"""
Buckaroo Application Wrapper

This module provides a high-level application wrapper for the Buckaroo SDK
that includes automatic logging setup, configuration management, and
convenient methods for common operations.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .services.payment_service import PaymentService
from .services.solution_service import SolutionService

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.observers import (
    BuckarooLoggingObserver,
    create_logger,
    create_logger_from_env,
    LogLevel,
    LogDestination,
    LogConfig,
)
from buckaroo.exceptions._authentication_error import AuthenticationError


@dataclass
class BuckarooConfig:
    """Configuration for Buckaroo Application."""

    # API Configuration
    store_key: Optional[str] = None
    secret_key: Optional[str] = None
    mode: str = "test"  # test or live

    # Logging Configuration
    enable_logging: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_destination: LogDestination = LogDestination.STDOUT
    log_file: str = "buckaroo_app.log"
    mask_sensitive_data: bool = True

    # SDK Configuration
    timeout: int = 30
    retry_attempts: int = 3

    @classmethod
    def from_env(cls) -> 'BuckarooConfig':
        """Create configuration from environment variables."""
        # Get log level from env
        log_level_str = os.getenv("BUCKAROO_LOG_LEVEL", "INFO").upper()
        log_level = (
            LogLevel(log_level_str)
            if log_level_str in [lv.value for lv in LogLevel]
            else LogLevel.INFO
        )

        # Get log destination from env
        log_dest_str = os.getenv("BUCKAROO_LOG_DESTINATION", "stdout").lower()

        log_destination = (
            LogDestination(log_dest_str)
            if log_dest_str in [d.value for d in LogDestination]
            else LogDestination.STDOUT
        )

        return cls(
            store_key=os.getenv("BUCKAROO_STORE_KEY"),
            secret_key=os.getenv("BUCKAROO_SECRET_KEY"),
            mode=os.getenv("BUCKAROO_MODE", "test"),
            log_level=log_level,
            log_destination=log_destination,
            log_file=os.getenv("BUCKAROO_LOG_FILE", "buckaroo_app.log"),
            mask_sensitive_data=os.getenv("BUCKAROO_LOG_MASK_SENSITIVE", "true").lower() == "true",
            timeout=int(os.getenv("BUCKAROO_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("BUCKAROO_RETRY_ATTEMPTS", "3")),
        )


class Buckaroo:
    """
    High-level Buckaroo SDK Application wrapper.

    This class provides a convenient interface for working with the Buckaroo SDK,
    including automatic logging setup, configuration management, and common operations.

    Example:
        >>> app = Buckaroo.from_env()
        >>> payment = app.create_ideal_payment(amount=25.50, currency="EUR")
        >>> response = app.execute_payment(payment)
    """
    
    def __init__(self, config: Optional[BuckarooConfig] = None):
        """
        Initialize Buckaroo Application.

        Args:
            config: Application configuration. If None, uses environment variables.
        """
        self.config = config or BuckarooConfig.from_env()
        self.logger: Optional[BuckarooLoggingObserver] = None
        self.client: Optional[BuckarooClient] = None

        # Initialize components
        self._setup_logging()
        self._setup_client()

    @classmethod
    def from_env(cls) -> "Buckaroo":
        """Create Buckaroo app from environment variables."""
        return cls(BuckarooConfig.from_env())
    
    @classmethod
    def quick_setup(
        cls, store_key: str, secret_key: str, mode: str = "test", log_to_stdout: bool = True
    ) -> "Buckaroo":
        """
        Quick setup for Buckaroo app with minimal configuration.

        Args:
            store_key: Buckaroo store key
            secret_key: Buckaroo secret key
            mode: API mode ("test" or "live")
            log_to_stdout: Whether to log to stdout (True) or file (False)

        Returns:
            Configured Buckaroo app
        """
        config = BuckarooConfig(
            store_key=store_key,
            secret_key=secret_key,
            mode=mode,
            log_destination=LogDestination.STDOUT if log_to_stdout else LogDestination.FILE,
        )
        return cls(config)

    def _setup_logging(self):
        """Setup logging based on configuration."""
        if not self.config.enable_logging:
            return

        log_config = LogConfig(
            level=self.config.log_level,
            destination=self.config.log_destination,
            log_file=self.config.log_file,
            mask_sensitive_data=self.config.mask_sensitive_data,
        )

        self.logger = BuckarooLoggingObserver(log_config)
        self.logger.log_info(
            "Buckaroo application initialized",
            mode=self.config.mode,
            log_level=self.config.log_level.value,
            log_destination=self.config.log_destination.value,
        )

    def _setup_client(self):
        """Setup Buckaroo client."""
        if not self.config.store_key or not self.config.secret_key:
            error_msg = "Store key and secret key are required"
            if self.logger:
                self.logger.log_error(
                    error_msg,
                    store_key_provided=bool(self.config.store_key),
                    secret_key_provided=bool(self.config.secret_key),
                )
            raise AuthenticationError(error_msg)

        try:
            self.client = BuckarooClient(
                self.config.store_key, self.config.secret_key, mode=self.config.mode
            )

            # Expose payments service directly on app for cleaner API
            self.payments = PaymentService(self.client)

            self.solutions = SolutionService(self.client)

            if self.logger:
                self.logger.log_info(
                    "Buckaroo client initialized successfully",
                    store_key_length=len(self.config.store_key),
                    mode=self.config.mode,
                )

        except Exception as e:
            if self.logger:
                self.logger.log_exception(e, context={"operation": "client_setup"})
            raise

    def log_info(self, message: str, **kwargs):
        """Log info message if logging is enabled."""
        if self.logger:
            self.logger.log_info(message, **kwargs)

    def log_debug(self, message: str, **kwargs):
        """Log debug message if logging is enabled."""
        if self.logger:
            self.logger.log_debug(message, **kwargs)

    def log_warning(self, message: str, **kwargs):
        """Log warning message if logging is enabled."""
        if self.logger:
            self.logger.log_warning(message, **kwargs)

    def log_error(self, message: str, **kwargs):
        """Log error message if logging is enabled."""
        if self.logger:
            self.logger.log_error(message, **kwargs)

    def log_exception(self, exception: Exception, **kwargs):
        """Log exception if logging is enabled."""
        if self.logger:
            self.logger.log_exception(exception, **kwargs)

    def get_client(self) -> BuckarooClient:
        """Get the underlying Buckaroo client."""
        if not self.client:
            raise RuntimeError("Client not initialized")
        return self.client

    def get_logger(self) -> Optional[BuckarooLoggingObserver]:
        """Get the logger instance."""
        return self.logger

    def create_child_logger(self, context: Dict[str, Any]):
        """Create a child logger with additional context."""
        if not self.logger:
            return None
        return self.logger.create_child_observer(context)

    def __enter__(self):
        """Context manager entry."""
        if self.logger:
            self.logger.log_debug("Entering Buckaroo app context")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.logger:
            if exc_type:
                self.logger.log_exception(exc_val, context={"context_manager": "exit"})
            else:
                self.logger.log_debug("Exiting Buckaroo app context successfully")

