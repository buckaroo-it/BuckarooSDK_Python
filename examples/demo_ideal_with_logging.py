#!/usr/bin/env python3
"""
Enhanced demo script showing different ways to create payments:
1. Dictionary parameters (quick setup)
2. Fluent interface (method chaining)  
3. Combined approach (dictionary + fluent)
4. Logging observer demonstration
"""

import json
import os
import sys

# Add parent directory to Python path to import buckaroo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.observers import create_logger, LogLevel, LogDestination


def demo_ideal_payments():
    """Demonstrate different ways to create iDEAL payments with logging."""
    # Setup logging observer
    print("Setting up logging observer...")
    
    # Create logger that logs to both stdout and file
    logger = create_logger(
        level=LogLevel.DEBUG,
        destination=LogDestination.BOTH,
        log_file="demo_payments.log",
        mask_sensitive_data=True
    )
    
    # Log demo start
    logger.log_info("Starting iDEAL payment demo", demo_version="1.0", user="demo_user")
    
    # Get credentials from environment variables
    store_key = os.getenv("BUCKAROO_STORE_KEY", "")
    secret_key = os.getenv("BUCKAROO_SECRET_KEY", "")
    
    if not store_key:
        error_msg = "BUCKAROO_STORE_KEY environment variable not set!"
        print(f"Warning: {error_msg}")
        print("Please set it using: export BUCKAROO_STORE_KEY='your_store_key'")
        logger.log_error(error_msg, required_env_vars=["BUCKAROO_STORE_KEY"])
        return
    
    if not secret_key:
        error_msg = "BUCKAROO_SECRET_KEY environment variable not set!"
        print(f"Warning: {error_msg}")
        print("Please set it using: export BUCKAROO_SECRET_KEY='your_secret_key'")
        logger.log_error(error_msg, required_env_vars=["BUCKAROO_SECRET_KEY"])
        return
    
    # Log successful credential retrieval
    logger.log_info("Credentials retrieved successfully", 
                   store_key_length=len(store_key),
                   secret_key_configured=bool(secret_key))
    
    try:
        client = BuckarooClient(store_key, secret_key, mode="test")
        logger.log_info("BuckarooClient initialized successfully", mode="test")
    except Exception as e:
        logger.log_exception(e, context={"operation": "client_initialization"})
        raise
    
    print("=" * 60)
    print("iDEAL PAYMENT EXAMPLES WITH LOGGING")
    print("=" * 60)
    
    # Method 1: Dictionary parameters (fastest for complete setup)
    print("\n1. Dictionary Parameters Approach:")
    print("-" * 40)
    
    # Log payment creation
    payment_data = {
        'currency': 'EUR',
        'amount': 6.0,
        'description': 'Automated test iDEAL with no issuer in the request',
        'invoice': 'Automatedtest_iDEAL_0013',
        'return_url': 'https://www.buckaroo.nl',
        'return_url_cancel': 'https://www.buckaroo.nl/annuleren',
        'return_url_error': 'https://www.buckaroo.nl/mislukt',
        'return_url_reject': 'https://www.buckaroo.nl/geweigerd',
        'continue_on_incomplete': '1',
        'client_ip': {'address': '0.0.0.0', 'type': 0},
        'issuer': 'ABNANL2A'  # iDEAL-specific parameter
    }
    
    logger.log_payment_operation(
        operation="create",
        payment_method="ideal",
        amount=payment_data['amount'],
        currency=payment_data['currency'],
        invoice=payment_data['invoice'],
        payment_data=payment_data
    )
    
    try:
        ideal = client.payments.create_payment("ideal", payment_data)
        logger.log_info("Payment object created successfully", payment_method="ideal")
        
        # Log payment execution attempt
        logger.log_info("Executing payment...", operation="execute")
        response = ideal.execute()  # Now makes actual HTTP request to Buckaroo API
        
        # Log payment response
        logger.log_payment_operation(
            operation="execute_response",
            payment_method="ideal",
            status="received",
            payment_key=getattr(response, 'payment_key', None),
            transaction_id=getattr(response, 'transaction_id', None)
        )

        # Check payment status and log results
        if response.is_pending():
            result_msg = f"Payment is pending. Redirect URL: {response.get_redirect_url()}"
            print(result_msg)
            logger.log_info("Payment is pending", 
                           redirect_url=response.get_redirect_url(),
                           payment_status="pending")
        elif response.is_successful():
            result_msg = f"Payment successful! Transaction ID: {response.get_transaction_id()}"
            print(result_msg)
            logger.log_info("Payment successful", 
                           transaction_id=response.get_transaction_id(),
                           payment_status="successful")
        elif response.is_failed():
            result_msg = f"Payment failed: {response.status.sub_code.description}"
            print(result_msg)
            logger.log_warning("Payment failed", 
                              error_description=response.status.sub_code.description,
                              payment_status="failed")

        # Access specific data and log it
        payment_details = {
            'payment_key': response.payment_key,
            'amount': f"{response.amount_debit} {response.currency}",
            'status_code': f"{response.status.code.code} - {response.status.code.description}"
        }
        
        print(f"Payment Key: {payment_details['payment_key']}")
        print(f"Amount: {payment_details['amount']}")
        print(f"Status Code: {payment_details['status_code']}")
        
        logger.log_info("Payment details retrieved", **payment_details)

        print("Payment executed successfully.")
        logger.log_info("Demo payment completed successfully")
        
    except Exception as e:
        error_msg = f"Payment execution failed: {str(e)}"
        print(f"Error: {error_msg}")
        logger.log_exception(e, context={
            "operation": "payment_execution",
            "payment_method": "ideal",
            "payment_data": payment_data
        })
    
    # Log demo completion
    logger.log_info("iDEAL payment demo completed", 
                   demo_section="dictionary_parameters",
                   status="completed")


if __name__ == "__main__":
    print("BUCKAROO PAYMENT SYSTEM - ENHANCED DEMO WITH LOGGING")
    print("=" * 80)
    
    # You can also create logger from environment variables
    # This allows runtime configuration via env vars:
    print("\nLogging Configuration:")
    print("- Set BUCKAROO_LOG_LEVEL=DEBUG for detailed logs")
    print("- Set BUCKAROO_LOG_DESTINATION=stdout for console only")
    print("- Set BUCKAROO_LOG_DESTINATION=file for file only") 
    print("- Set BUCKAROO_LOG_FILE=custom.log for custom log file")
    print("- Set BUCKAROO_LOG_MASK_SENSITIVE=false to disable data masking")
    print()
    
    try:
        demo_ideal_payments()
    except Exception as e:
        print(f"Demo failed with error: {e}")
        # Even if the main demo fails, we can still log it
        from buckaroo.observers import create_logger_from_env
        fallback_logger = create_logger_from_env()
        fallback_logger.log_exception(e, context={"demo": "ideal_payments", "stage": "main"})
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETED")
    print("Check 'demo_payments.log' file for detailed logs")
    print("=" * 80)