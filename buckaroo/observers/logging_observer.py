"""
Logging observer for Buckaroo SDK.

This module provides comprehensive logging capabilities for HTTP requests,
responses, exceptions, and general SDK operations. It supports both file
and stdout logging with configurable log levels and formats.
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass


class LogLevel(Enum):
    """Log levels for the observer."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogDestination(Enum):
    """Log output destinations."""
    STDOUT = "stdout"
    FILE = "file"
    BOTH = "both"


@dataclass
class LogConfig:
    """Configuration for logging observer."""
    level: LogLevel = LogLevel.INFO
    destination: LogDestination = LogDestination.BOTH
    log_file: str = "buckaroo_sdk.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    include_request_body: bool = True
    include_response_body: bool = True
    mask_sensitive_data: bool = True
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class BuckarooLoggingObserver:
    """
    Comprehensive logging observer for Buckaroo SDK operations.
    
    This class provides detailed logging for HTTP requests, responses,
    exceptions, and other SDK operations with support for multiple
    output destinations and configurable formatting.
    """
    
    def __init__(self, config: Optional[LogConfig] = None):
        """
        Initialize the logging observer.
        
        Args:
            config: Optional logging configuration. Uses defaults if not provided.
        """
        self.config = config or LogConfig()
        self.logger = self._setup_logger()
        self._sensitive_fields = {
            'secret_key', 'password', 'token', 'authorization', 'cvv',
            'cardnumber', 'card_number', 'iban', 'account_number',
            'store_key', 'x-buckaroo-store-key',
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with configured handlers and formatters."""
        logger = logging.getLogger("buckaroo_sdk")
        logger.setLevel(getattr(logging, self.config.level.value))
        
        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()
        
        formatter = logging.Formatter(
            fmt=self.config.log_format,
            datefmt=self.config.date_format
        )
        
        # Setup stdout handler
        if self.config.destination in [LogDestination.STDOUT, LogDestination.BOTH]:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(formatter)
            logger.addHandler(stdout_handler)
        
        # Setup file handler
        if self.config.destination in [LogDestination.FILE, LogDestination.BOTH]:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                filename=self.config.log_file,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """
        Recursively mask sensitive data in dictionaries and strings.
        
        Args:
            data: Data to mask (dict, list, str, or other)
            
        Returns:
            Data with sensitive fields masked
        """
        if not self.config.mask_sensitive_data:
            return data
        
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in self._sensitive_fields):
                    masked[key] = "***MASKED***"
                else:
                    masked[key] = self._mask_sensitive_data(value)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            # Basic masking for potential sensitive data in strings
            if any(sensitive in data.lower() for sensitive in self._sensitive_fields):
                return "***POTENTIALLY_SENSITIVE***"
            return data
        else:
            return data
    
    def _format_json(self, data: Any) -> str:
        """Format data as pretty JSON string."""
        try:
            if isinstance(data, str):
                # Try to parse if it's a JSON string
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return data
            
            masked_data = self._mask_sensitive_data(data)
            return json.dumps(masked_data, indent=2, default=str)
        except Exception:
            return str(data)
    
    def log_request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, 
                   body: Optional[Any] = None, **kwargs):
        """
        Log HTTP request details.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            body: Request body
            **kwargs: Additional context data
        """
        request_id = kwargs.get('request_id', self._generate_request_id())
        
        log_message = [
            f"HTTP REQUEST [{request_id}]",
            f"Method: {method}",
            f"URL: {url}"
        ]
        
        if headers:
            masked_headers = self._mask_sensitive_data(headers)
            log_message.append(f"Headers: {self._format_json(masked_headers)}")
        
        if body and self.config.include_request_body:
            log_message.append(f"Body: {self._format_json(body)}")
        
        if kwargs:
            log_message.append(f"Context: {self._format_json(kwargs)}")
        
        self.logger.info("\n".join(log_message))
    
    def log_response(self, status_code: int, headers: Optional[Dict[str, str]] = None,
                    body: Optional[Any] = None, duration_ms: Optional[float] = None,
                    **kwargs):
        """
        Log HTTP response details.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            body: Response body
            duration_ms: Request duration in milliseconds
            **kwargs: Additional context data
        """
        request_id = kwargs.get('request_id', 'unknown')
        
        log_message = [
            f"HTTP RESPONSE [{request_id}]",
            f"Status: {status_code}"
        ]
        
        if duration_ms is not None:
            log_message.append(f"Duration: {duration_ms:.2f}ms")
        
        if headers:
            masked_headers = self._mask_sensitive_data(headers)
            log_message.append(f"Headers: {self._format_json(masked_headers)}")
        
        if body and self.config.include_response_body:
            log_message.append(f"Body: {self._format_json(body)}")
        
        if kwargs:
            log_message.append(f"Context: {self._format_json(kwargs)}")
        
        # Log as info for success, warning for client errors, error for server errors
        if 200 <= status_code < 300:
            self.logger.info("\n".join(log_message))
        elif 400 <= status_code < 500:
            self.logger.warning("\n".join(log_message))
        else:
            self.logger.error("\n".join(log_message))
    
    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None,
                     **kwargs):
        """
        Log exception details with context.
        
        Args:
            exception: The exception to log
            context: Additional context information
            **kwargs: Additional context data
        """
        request_id = kwargs.get('request_id', 'unknown')
        
        log_message = [
            f"EXCEPTION [{request_id}]",
            f"Type: {type(exception).__name__}",
            f"Message: {str(exception)}"
        ]
        
        if context:
            log_message.append(f"Context: {self._format_json(context)}")
        
        if kwargs:
            log_message.append(f"Additional Info: {self._format_json(kwargs)}")
        
        # Include stack trace for debug level
        import traceback
        if self.logger.isEnabledFor(logging.DEBUG):
            log_message.append(f"Stack Trace:\n{traceback.format_exc()}")
        
        self.logger.error("\n".join(log_message))
    
    def log_payment_operation(self, operation: str, payment_method: str, 
                             amount: Optional[float] = None, currency: Optional[str] = None,
                             **kwargs):
        """
        Log payment-specific operations.
        
        Args:
            operation: Operation type (create, execute, validate, etc.)
            payment_method: Payment method (ideal, creditcard, etc.)
            amount: Payment amount
            currency: Payment currency
            **kwargs: Additional payment data
        """
        request_id = kwargs.get('request_id', self._generate_request_id())
        
        log_message = [
            f"PAYMENT OPERATION [{request_id}]",
            f"Operation: {operation}",
            f"Method: {payment_method}"
        ]
        
        if amount is not None:
            log_message.append(f"Amount: {amount}")
        
        if currency:
            log_message.append(f"Currency: {currency}")
        
        if kwargs:
            masked_kwargs = self._mask_sensitive_data(kwargs)
            log_message.append(f"Details: {self._format_json(masked_kwargs)}")
        
        self.logger.info("\n".join(log_message))
    
    def log_config_change(self, config_name: str, old_value: Any, new_value: Any, **kwargs):
        """
        Log configuration changes.
        
        Args:
            config_name: Name of the configuration parameter
            old_value: Previous value
            new_value: New value
            **kwargs: Additional context
        """
        log_message = [
            "CONFIG CHANGE",
            f"Parameter: {config_name}",
            f"Old Value: {self._mask_sensitive_data(old_value)}",
            f"New Value: {self._mask_sensitive_data(new_value)}"
        ]
        
        if kwargs:
            log_message.append(f"Context: {self._format_json(kwargs)}")
        
        self.logger.info("\n".join(log_message))
    
    def log_info(self, message: str, **kwargs):
        """Log general information message."""
        self._log_with_context("INFO", message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context("DEBUG", message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context("WARNING", message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_context("ERROR", message, **kwargs)
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with context at specified level."""
        request_id = kwargs.get('request_id', '')
        prefix = f"[{request_id}] " if request_id else ""
        
        full_message = f"{prefix}{message}"
        
        if kwargs:
            full_message += f"\nContext: {self._format_json(kwargs)}"
        
        getattr(self.logger, level.lower())(full_message)
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        from uuid import uuid4
        return str(uuid4())[:8]
    
    def create_child_observer(self, context: Dict[str, Any]) -> 'ContextualLoggingObserver':
        """
        Create a child observer with additional context.
        
        Args:
            context: Context to be included in all log messages
            
        Returns:
            A contextual logging observer
        """
        return ContextualLoggingObserver(self, context)


class ContextualLoggingObserver:
    """
    A wrapper around BuckarooLoggingObserver that includes context in all log messages.
    """
    
    def __init__(self, parent: BuckarooLoggingObserver, context: Dict[str, Any]):
        """
        Initialize contextual observer.
        
        Args:
            parent: Parent logging observer
            context: Context to include in all messages
        """
        self.parent = parent
        self.context = context
    
    def log_request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                   body: Optional[Any] = None, **kwargs):
        """Log request with context."""
        merged_kwargs = {**self.context, **kwargs}
        self.parent.log_request(method, url, headers, body, **merged_kwargs)
    
    def log_response(self, status_code: int, headers: Optional[Dict[str, str]] = None,
                    body: Optional[Any] = None, duration_ms: Optional[float] = None,
                    **kwargs):
        """Log response with context."""
        merged_kwargs = {**self.context, **kwargs}
        self.parent.log_response(status_code, headers, body, duration_ms, **merged_kwargs)
    
    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None,
                     **kwargs):
        """Log exception with context."""
        merged_context = {**self.context}
        if context:
            merged_context.update(context)
        merged_kwargs = {**kwargs}
        self.parent.log_exception(exception, merged_context, **merged_kwargs)
    
    def log_payment_operation(self, operation: str, payment_method: str,
                             amount: Optional[float] = None, currency: Optional[str] = None,
                             **kwargs):
        """Log payment operation with context."""
        merged_kwargs = {**self.context, **kwargs}
        self.parent.log_payment_operation(operation, payment_method, amount, currency,
                                        **merged_kwargs)
    
    def log_info(self, message: str, **kwargs):
        """Log info with context."""
        merged_kwargs = {**self.context, **kwargs}
        self.parent.log_info(message, **merged_kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug with context."""
        merged_kwargs = {**self.context, **kwargs}
        self.parent.log_debug(message, **merged_kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning with context."""
        merged_kwargs = {**self.context, **kwargs}
        self.parent.log_warning(message, **merged_kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error with context."""
        merged_kwargs = {**self.context, **kwargs}
        self.parent.log_error(message, **merged_kwargs)


def create_logger(level: LogLevel = LogLevel.INFO,
                 destination: LogDestination = LogDestination.BOTH,
                 log_file: str = "buckaroo.log",
                 **kwargs) -> BuckarooLoggingObserver:
    """
    Convenience function to create a logging observer.
    
    Args:
        level: Log level
        destination: Where to send logs
        log_file: Log file name (if file logging enabled)
        **kwargs: Additional configuration options
        
    Returns:
        Configured logging observer
    """
    config = LogConfig(
        level=level,
        destination=destination,
        log_file=log_file,
        **kwargs
    )
    return BuckarooLoggingObserver(config)


def create_logger_from_env() -> BuckarooLoggingObserver:
    """
    Create logger from environment variables.
    
    Environment variables:
        BUCKAROO_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        BUCKAROO_LOG_DESTINATION: Destination (stdout, file, both)
        BUCKAROO_LOG_FILE: Log file path
        BUCKAROO_LOG_MASK_SENSITIVE: Whether to mask sensitive data (true/false)
        
    Returns:
        Configured logging observer
    """
    level_str = os.getenv("BUCKAROO_LOG_LEVEL", "INFO").upper()
    level = LogLevel(level_str) if level_str in [l.value for l in LogLevel] else LogLevel.INFO
    
    dest_str = os.getenv("BUCKAROO_LOG_DESTINATION", "both").lower()
    destination = LogDestination(dest_str) if dest_str in [d.value for d in LogDestination] else LogDestination.BOTH
    
    log_file = os.path.basename(os.getenv("BUCKAROO_LOG_FILE", "buckaroo_sdk.log"))
    mask_sensitive = os.getenv("BUCKAROO_LOG_MASK_SENSITIVE", "true").lower() == "true"
    
    config = LogConfig(
        level=level,
        destination=destination,
        log_file=log_file,
        mask_sensitive_data=mask_sensitive
    )
    
    return BuckarooLoggingObserver(config)