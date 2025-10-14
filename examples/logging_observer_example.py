#!/usr/bin/env python3
"""
Logging observer example for Buckaroo SDK.

This example demonstrates how to use the logging observer to monitor
HTTP requests, responses, exceptions, and other SDK operations.
"""

import os
import sys

# Add parent directory to Python path to import buckaroo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buckaroo.observers import (
    create_logger, 
    create_logger_from_env,
    LogLevel, 
    LogDestination,
    LogConfig,
    BuckarooLoggingObserver
)


def basic_logging_example():
    """Demonstrate basic logging functionality."""
    print("=== Basic Logging Example ===")
    
    # Create a logger with custom configuration
    logger = create_logger(
        level=LogLevel.DEBUG,
        destination=LogDestination.BOTH,
        log_file="example_logs.log"
    )
    
    # Basic logging
    logger.log_info("Starting basic logging example")
    logger.log_debug("This is a debug message", component="example")
    logger.log_warning("This is a warning message", severity="medium")
    logger.log_error("This is an error message", error_code="E001")
    
    # Log with context
    logger.log_info("Processing payment", 
                   payment_id="PAY-123",
                   amount=25.50,
                   currency="EUR")


def request_response_logging_example():
    """Demonstrate HTTP request/response logging."""
    print("\n=== Request/Response Logging Example ===")
    
    logger = create_logger(level=LogLevel.INFO)
    
    # Simulate logging HTTP request
    logger.log_request(
        method="POST",
        url="https://testcheckout.buckaroo.nl/json/Transaction",
        headers={
            "Authorization": "hmac_secret_key_signature",
            "Content-Type": "application/json",
            "User-Agent": "BuckarooSDK/1.0"
        },
        body={
            "Currency": "EUR",
            "AmountDebit": 10.00,
            "Invoice": "TEST-001",
            "Services": {
                "ServiceList": [
                    {
                        "Name": "ideal",
                        "Action": "Pay",
                        "Parameters": [
                            {"Name": "issuer", "Value": "ABNANL2A"}
                        ]
                    }
                ]
            }
        },
        request_id="req_123456"
    )
    
    # Simulate logging HTTP response
    logger.log_response(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "X-Request-ID": "req_123456"
        },
        body={
            "Key": "payment_key_123",
            "Status": {
                "Code": {"Code": 790, "Description": "Pending processing"},
                "SubCode": {"Code": 790, "Description": "Pending processing"}
            },
            "RequiredAction": {
                "RedirectURL": "https://payment.buckaroo.nl/redirect/123"
            }
        },
        duration_ms=250.5,
        request_id="req_123456"
    )


def exception_logging_example():
    """Demonstrate exception logging."""
    print("\n=== Exception Logging Example ===")
    
    logger = create_logger(level=LogLevel.ERROR)
    
    # Simulate different types of exceptions
    try:
        # Simulate authentication error
        raise ValueError("Invalid API credentials provided")
    except Exception as e:
        logger.log_exception(e, context={
            "operation": "authentication",
            "store_key": "test_key_***",
            "api_endpoint": "https://testcheckout.buckaroo.nl"
        })
    
    try:
        # Simulate network error
        raise ConnectionError("Failed to connect to Buckaroo API")
    except Exception as e:
        logger.log_exception(e, context={
            "operation": "http_request",
            "retry_attempt": 3,
            "max_retries": 5
        })


def payment_operation_logging_example():
    """Demonstrate payment operation logging."""
    print("\n=== Payment Operation Logging Example ===")
    
    logger = create_logger(level=LogLevel.INFO)
    
    # Log payment creation
    logger.log_payment_operation(
        operation="create",
        payment_method="ideal",
        amount=15.50,
        currency="EUR",
        invoice="INV-001",
        issuer="ABNANL2A",
        description="Test payment"
    )
    
    # Log payment execution
    logger.log_payment_operation(
        operation="execute",
        payment_method="ideal",
        payment_key="PAY-123",
        status="pending",
        redirect_url="https://payment.buckaroo.nl/redirect/123"
    )
    
    # Log payment result
    logger.log_payment_operation(
        operation="result",
        payment_method="ideal",
        payment_key="PAY-123",
        status="successful",
        transaction_id="TXN-456",
        amount_paid=15.50
    )


def contextual_logging_example():
    """Demonstrate contextual logging with child observers."""
    print("\n=== Contextual Logging Example ===")
    
    # Create main logger
    main_logger = create_logger(level=LogLevel.INFO)
    
    # Create contextual logger for a specific payment session
    payment_context = {
        "session_id": "sess_789",
        "user_id": "user_123",
        "payment_method": "ideal"
    }
    
    contextual_logger = main_logger.create_child_observer(payment_context)
    
    # All logs from contextual logger will include the context
    contextual_logger.log_info("Starting payment process")
    contextual_logger.log_info("Validating payment data", amount=25.00, currency="EUR")
    contextual_logger.log_info("Payment completed successfully", transaction_id="TXN-789")


def environment_configuration_example():
    """Demonstrate environment-based configuration."""
    print("\n=== Environment Configuration Example ===")
    
    # Set environment variables for demonstration
    os.environ["BUCKAROO_LOG_LEVEL"] = "DEBUG"
    os.environ["BUCKAROO_LOG_DESTINATION"] = "stdout"
    os.environ["BUCKAROO_LOG_MASK_SENSITIVE"] = "true"
    
    # Create logger from environment
    env_logger = create_logger_from_env()
    
    env_logger.log_info("Logger created from environment variables")
    env_logger.log_debug("Debug logging enabled via environment")
    
    # Log sensitive data (will be masked)
    env_logger.log_info("Processing payment with sensitive data", 
                       credit_card_number="4111111111111111",  # Will be masked
                       cvv="123",  # Will be masked
                       amount=50.00)  # Will not be masked


def advanced_configuration_example():
    """Demonstrate advanced logging configuration."""
    print("\n=== Advanced Configuration Example ===")
    
    # Create custom configuration
    config = LogConfig(
        level=LogLevel.DEBUG,
        destination=LogDestination.FILE,
        log_file="advanced_example.log",
        max_file_size=1024 * 1024,  # 1MB
        backup_count=3,
        include_request_body=True,
        include_response_body=False,  # Exclude response bodies
        mask_sensitive_data=True,
        log_format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        date_format="%Y-%m-%d %H:%M:%S"
    )
    
    # Create logger with custom config
    advanced_logger = BuckarooLoggingObserver(config)
    
    advanced_logger.log_info("Advanced logger configuration active")
    advanced_logger.log_debug("Custom format and file rotation enabled")
    
    # This request body will be logged, but response body won't be
    advanced_logger.log_request(
        method="POST",
        url="https://api.example.com/payment",
        body={"amount": 100, "currency": "EUR"}
    )
    
    advanced_logger.log_response(
        status_code=200,
        body={"result": "success", "large_data": "..." * 1000}  # Won't be logged
    )


def main():
    """Run all logging examples."""
    print("BUCKAROO SDK LOGGING OBSERVER EXAMPLES")
    print("=" * 60)
    
    basic_logging_example()
    request_response_logging_example()
    exception_logging_example()
    payment_operation_logging_example()
    contextual_logging_example()
    environment_configuration_example()
    advanced_configuration_example()
    
    print("\n" + "=" * 60)
    print("LOGGING EXAMPLES COMPLETED")
    print("Check the following log files:")
    print("- example_logs.log")
    print("- advanced_example.log") 
    print("=" * 60)


if __name__ == "__main__":
    main()