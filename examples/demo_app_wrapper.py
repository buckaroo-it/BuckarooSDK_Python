#!/usr/bin/env python3
"""
Simplified demo using Buckaroo App wrapper.

This demo shows how to use the BuckarooApp wrapper which handles
logging initialization automatically and provides convenient methods.
"""

import os
import sys

# Add parent directory to Python path to import buckaroo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buckaroo.app import Buckaroo, BuckarooConfig
from buckaroo.observers import LogLevel, LogDestination


def demo_with_app_wrapper():
    """Demonstrate payments using the Buckaroo app wrapper."""
    
    print("BUCKAROO APP WRAPPER DEMO")
    print("=" * 50)
    
    # Method 1: Quick setup (minimal configuration)
    print("\n1. Quick Setup Demo:")
    print("-" * 30)
    
    store_key = os.getenv("BUCKAROO_STORE_KEY")
    secret_key = os.getenv("BUCKAROO_SECRET_KEY")
    
    if not store_key or not secret_key:
        print("⚠️  Please set BUCKAROO_STORE_KEY and BUCKAROO_SECRET_KEY environment variables")
        return
    
    try:
        # Quick setup - logger is automatically initialized
        app = Buckaroo()

        # Logger is already available, no need to initialize
        app.log_info("Quick setup demo started")
        
        # Create iDEAL payment using factory pattern - auto-detected by 'issuer' field
        payment = app.payments.create({
            "method": "bancontact",
            "amount": 25.50,
            "currency": "EUR", 
            "invoice": "QUICK-001",
            "description": "Quick setup demo payment",
            "return_url": "https://www.buckaroo.nl",
            "return_url_cancel": "https://www.buckaroo.nl/cancel",
            "return_url_error": "https://www.buckaroo.nl/error", 
            "return_url_reject": "https://www.buckaroo.nl/reject",
            "original_transaction_key": "TXN_123",
            "PaymentData": "Lorem",
            "CustomerCardName": "Ipsum",
            "issuer": "ABNANL2A"
        })

        response = payment.pay()
        print(response.to_dict())
        # Execute refund - values from payload (no parameters needed)
        # response = payment.refund()  # Uses original_transaction_key and refund_amount from payload
        # print(response)
        # Or override payload values with parameters
        # response = payment.refund("DIFFERENT_TXN_123", 10.00)  # Override with specific values
        
        print(f"✅ Payment builder created: {type(payment).__name__}")
        print("   Methods can use payload values or parameters:")
        print("   - payment.execute() for new payment")
        print("   - payment.refund() uses payload 'original_transaction_key' and 'refund_amount'") 
        print("   - payment.refund('TXN_KEY', amount) to override payload values")
        print("   - payment.capture() uses payload 'authorization_key' and 'capture_amount'")
        print("   - payment.cancel() uses payload 'cancel_key' or 'original_transaction_key'")
        
        # Show payload values that would be used
        print(f"\n   Payload values available:")
        print(f"   - original_transaction_key: {payment._payload.get('original_transaction_key')}")
        print(f"   - refund_amount: {payment._payload.get('refund_amount')}")
        print(f"   - issuer: {payment._payload.get('issuer')}")
        
        # # Show additional payload examples
        # print("\n   Additional payload examples:")
        
        # # Capture example with payload values
        # capture_payment = app.payments.create({
        #     "amount": 100.00,
        #     "currency": "EUR", 
        #     "invoice": "CAPTURE-001",
        #     "description": "Capture demo",
        #     "return_url": "https://www.buckaroo.nl",
        #     "return_url_cancel": "https://www.buckaroo.nl/cancel", 
        #     "return_url_error": "https://www.buckaroo.nl/error",
        #     "return_url_reject": "https://www.buckaroo.nl/reject",
        #     "authorization_key": "AUTH_456",  # For capture operations
        #     "capture_amount": 75.00,           # Partial capture amount
        #     "card_number": "1234567890123456"  # Credit card payment
        # })
        # print("   Created capture payment with authorization_key and capture_amount")
        # print(f"   - Authorization key: {capture_payment._payload.get('authorization_key')}")
        # print(f"   - Capture amount: {capture_payment._payload.get('capture_amount')}")
        # # capture_payment.capture()  # Would use AUTH_456 and 75.00 from payload
        
        # # Cancel example with payload values  
        # cancel_payment = app.payments.create({
        #     "amount": 50.00,
        #     "currency": "EUR",
        #     "invoice": "CANCEL-001", 
        #     "description": "Cancel demo",
        #     "return_url": "https://www.buckaroo.nl",
        #     "return_url_cancel": "https://www.buckaroo.nl/cancel",
        #     "return_url_error": "https://www.buckaroo.nl/error", 
        #     "return_url_reject": "https://www.buckaroo.nl/reject",
        #     "cancel_key": "PENDING_789",       # For cancel operations
        #     "issuer": "ABNANL2A"
        # })
        # print("   Created cancel payment with cancel_key")
        # print(f"   - Cancel key: {cancel_payment._payload.get('cancel_key')}")
        # # cancel_payment.cancel()  # Would use PENDING_789 from payload
        
        app.log_info("Quick setup demo completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'app' in locals():
            app.log_exception(e)


def demo_with_environment_config():
    """Demonstrate using environment-based configuration."""
    
    print("\n2. Environment Configuration Demo:")
    print("-" * 40)
    
    try:
        # Create app from environment variables
        # This automatically reads all BUCKAROO_* environment variables
        app = Buckaroo.from_env()
        
        app.log_info("Environment-based app started")
        
        # Create payment using the generic method
        payment_data = {
            'currency': 'EUR',
            'amount': 15.75,
            'description': 'Environment config demo',
            'invoice': 'ENV-DEMO-001',
            'return_url': 'https://www.buckaroo.nl',
            'return_url_cancel': 'https://www.buckaroo.nl/cancel',
            'return_url_error': 'https://www.buckaroo.nl/error',
            'return_url_reject': 'https://www.buckaroo.nl/reject',
            'issuer': 'ABNANL2A'
        }
        
        payment = app.create_payment("ideal", payment_data)
        response = app.execute_payment(payment)
        
        print("✅ Environment-based configuration worked!")
        app.log_info("Environment demo completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'app' in locals():
            app.log_exception(e)


def demo_with_custom_config():
    """Demonstrate using custom configuration."""
    
    print("\n3. Custom Configuration Demo:")
    print("-" * 35)
    
    store_key = os.getenv("BUCKAROO_STORE_KEY")
    secret_key = os.getenv("BUCKAROO_SECRET_KEY")
    
    if not store_key or not secret_key:
        print("⚠️  Skipping - credentials not available")
        return
    
    try:
        # Create custom configuration
        config = BuckarooConfig(
            store_key=store_key,
            secret_key=secret_key,
            mode="test",
            enable_logging=True,
            log_level=LogLevel.DEBUG,
            log_destination=LogDestination.STDOUT,
            mask_sensitive_data=True,
            timeout=45,
            retry_attempts=5
        )
        
        app = Buckaroo(config)
        
        app.log_info("Custom configuration demo started")
        
        # Create payment with child logger (adds context to all logs)
        session_context = {
            "session_id": "sess_custom_001",
            "user_id": "demo_user",
            "demo_type": "custom_config"
        }
        
        child_logger = app.create_child_logger(session_context)
        
        if child_logger:
            child_logger.log_info("Starting payment with custom context")
        
        payment = app.create_ideal_payment(
            amount=42.00,
            currency="EUR",
            description="Custom config demo payment",
            invoice="CUSTOM-001"
        )
        
        response = app.execute_payment(payment)
        
        print("✅ Custom configuration demo completed!")
        app.log_info("Custom config demo finished")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'app' in locals():
            app.log_exception(e)


def demo_with_context_manager():
    """Demonstrate using app as context manager."""
    
    print("\n4. Context Manager Demo:")
    print("-" * 30)
    
    store_key = os.getenv("BUCKAROO_STORE_KEY")
    secret_key = os.getenv("BUCKAROO_SECRET_KEY")
    
    if not store_key or not secret_key:
        print("⚠️  Skipping - credentials not available")
        return
    
    try:
        # Use app as context manager
        with Buckaroo.quick_setup(store_key, secret_key, log_to_stdout=True) as app:
            app.log_info("Context manager demo started")
            
            # Multiple operations within the context
            for i in range(2):
                app.log_info(f"Creating payment {i+1}")
                
                payment = app.create_ideal_payment(
                    amount=10.00 + i,
                    currency="EUR",
                    description=f"Context demo payment {i+1}",
                    invoice=f"CTX-{i+1:03d}"
                )
                
                # Simulate processing
                app.log_info(f"Processing payment {i+1}")
        
        print("✅ Context manager demo completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all demos."""
    print("BUCKAROO SDK - APP WRAPPER DEMOS")
    print("=" * 60)
    
    print("\n📋 Available Logging Environment Variables:")
    print("- BUCKAROO_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR")
    print("- BUCKAROO_LOG_DESTINATION=stdout|file|both")
    print("- BUCKAROO_LOG_FILE=custom.log")
    print("- BUCKAROO_LOG_MASK_SENSITIVE=true|false")
    
    demo_with_app_wrapper()
    # demo_with_environment_config()
    # demo_with_custom_config()
    # demo_with_context_manager()
    
    print("\n" + "=" * 60)
    print("🎉 ALL DEMOS COMPLETED!")
    print("The Buckaroo wrapper automatically handles:")
    print("✅ Logging initialization")
    print("✅ Client setup") 
    print("✅ Automatic payment logging")
    print("✅ Exception handling")
    print("✅ Environment configuration")
    print("=" * 60)


if __name__ == "__main__":
    main()