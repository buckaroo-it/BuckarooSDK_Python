#!/usr/bin/env python3
"""
Factory Pattern Payment Demo

This demo shows how to use the new factory pattern with app.payments.create({payload})
that automatically detects payment methods based on payload content.
"""

import os
import sys

# Add parent directory to Python path to import buckaroo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buckaroo.app import Buckaroo


def demo_factory_pattern():
    """Demonstrate the factory pattern for payment creation."""
    
    print("FACTORY PATTERN PAYMENT DEMO")
    print("=" * 50)
    
    # Setup app
    app = Buckaroo()
    app.log_info("Factory pattern demo started")
    
    print("\n1. iDEAL Payment (auto-detected by 'issuer' field):")
    print("-" * 55)
    
    try:
        # iDEAL payment - detected automatically by 'issuer' field
        ideal_payment = app.payment.create({
            "amount": 25.50,
            "currency": "EUR",
            "description": "iDEAL payment via factory",
            "invoice": "IDEAL-001",
            "return_url": "https://www.buckaroo.nl",
            "return_url_cancel": "https://www.buckaroo.nl/cancel",
            "return_url_error": "https://www.buckaroo.nl/error",
            "return_url_reject": "https://www.buckaroo.nl/reject",
            "issuer": "ABNANL2A"  # This triggers iDEAL detection
        })
        
        print(f"✅ Created iDEAL payment builder: {type(ideal_payment).__name__}")
        app.log_info("iDEAL payment created successfully via factory")
        
    except Exception as e:
        print(f"❌ iDEAL Error: {e}")
        app.log_exception(e)
    
    print("\n2. Credit Card Payment (auto-detected by card fields):")
    print("-" * 60)
    
    try:
        # Credit card payment - detected by card number field
        card_payment = app.payment.create({
            "amount": 42.00,
            "currency": "USD",
            "description": "Credit card payment via factory",
            "invoice": "CC-002",
            "return_url": "https://www.buckaroo.nl",
            "card_number": "4111111111111111",  # This triggers credit card detection
            "expiry_month": "12",
            "expiry_year": "2025",
            "cvv": "123",
            "cardholder_name": "John Doe"
        })
        
        print(f"✅ Created credit card payment builder: {type(card_payment).__name__}")
        app.log_info("Credit card payment created successfully via factory")
        
    except Exception as e:
        print(f"❌ Credit Card Error: {e}")
        app.log_exception(e)
    
    print("\n3. PayPal Payment (explicit method specification):")
    print("-" * 55)
    
    try:
        # PayPal payment - explicitly specified
        paypal_payment = app.payment.create({
            "payment_method": "paypal",  # Explicit method specification
            "amount": 15.75,
            "currency": "EUR",
            "description": "PayPal payment via factory",
            "invoice": "PP-003",
            "return_url": "https://www.buckaroo.nl"
        })
        
        print(f"✅ Created PayPal payment builder: {type(paypal_payment).__name__}")
        app.log_info("PayPal payment created successfully via factory")
        
    except Exception as e:
        print(f"❌ PayPal Error: {e}")
        app.log_exception(e)
    
    print("\n4. Apple Pay Payment (auto-detected by payment data):")
    print("-" * 58)
    
    try:
        # Apple Pay payment - detected by payment_data field
        applepay_payment = app.payment.create({
            "amount": 99.99,
            "currency": "USD",
            "description": "Apple Pay payment via factory",
            "invoice": "AP-004",
            "return_url": "https://www.buckaroo.nl",
            "payment_data": "base64_encoded_apple_pay_token"  # This triggers Apple Pay detection
        })
        
        print(f"✅ Created Apple Pay payment builder: {type(applepay_payment).__name__}")
        app.log_info("Apple Pay payment created successfully via factory")
        
    except Exception as e:
        print(f"❌ Apple Pay Error: {e}")
        app.log_exception(e)
    
    print("\n5. iDEAL QR Payment (explicit service specification):")
    print("-" * 58)
    
    try:
        # iDEAL QR payment - explicitly specified
        idealqr_payment = app.payment.create({
            "service": "idealqr",  # Another way to specify method
            "amount": 8.50,
            "currency": "EUR",
            "description": "iDEAL QR payment via factory",
            "invoice": "QR-005"
        })
        
        print(f"✅ Created iDEAL QR payment builder: {type(idealqr_payment).__name__}")
        app.log_info("iDEAL QR payment created successfully via factory")
        
    except Exception as e:
        print(f"❌ iDEAL QR Error: {e}")
        app.log_exception(e)


def demo_factory_error_handling():
    """Demonstrate error handling with the factory pattern."""
    
    print("\n" + "=" * 50)
    print("FACTORY ERROR HANDLING DEMO")
    print("=" * 50)
    
    app = Buckaroo()
    
    print("\n6. Ambiguous Payload (should raise error):")
    print("-" * 45)
    
    try:
        # This payload doesn't have clear payment method indicators
        ambiguous_payment = app.payment.create({
            "amount": 10.00,
            "currency": "EUR",
            "description": "Ambiguous payment method"
            # No method indicators like 'issuer', 'card_number', etc.
        })
        
        print(f"❌ Should have failed but got: {type(ambiguous_payment).__name__}")
        
    except ValueError as e:
        print(f"✅ Correctly caught ambiguous payload: {e}")
        app.log_info("Ambiguous payload correctly rejected")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        app.log_exception(e)


def show_available_methods():
    """Show all available payment methods."""
    
    print("\n" + "=" * 50)
    print("AVAILABLE PAYMENT METHODS")
    print("=" * 50)
    
    app = Buckaroo()
    
    try:
        methods = app.payment.get_available_methods()
        print(f"\n📋 Available payment methods: {', '.join(methods)}")
        
        # Test method support
        test_methods = ["ideal", "creditcard", "paypal", "bitcoin", "applepay"]
        
        print(f"\n🔍 Method support check:")
        for method in test_methods:
            supported = app.payment.is_method_supported(method)
            status = "✅" if supported else "❌"
            print(f"   {status} {method}: {'Supported' if supported else 'Not supported'}")
            
    except Exception as e:
        print(f"❌ Error checking methods: {e}")
        app.log_exception(e)


def main():
    """Run all factory pattern demos."""
    
    print("BUCKAROO SDK - FACTORY PATTERN DEMOS")
    print("=" * 60)
    
    print("\n📋 Factory Pattern Benefits:")
    print("✅ Automatic payment method detection from payload")
    print("✅ Cleaner, more intuitive API: app.payment.create({payload})")
    print("✅ Extensible - easy to add new payment methods")
    print("✅ Explicit method specification still supported")
    print("✅ Comprehensive error handling")
    
    demo_factory_pattern()
    demo_factory_error_handling()
    show_available_methods()
    
    print("\n" + "=" * 60)
    print("🎉 FACTORY PATTERN DEMO COMPLETED!")
    print("\nFactory Detection Rules:")
    print("• iDEAL: Presence of 'issuer' field")
    print("• Credit Card: Presence of card fields (card_number, expiry_month, etc.)")
    print("• Apple Pay: Presence of 'payment_data' or 'apple_pay_token'")
    print("• PayPal: PayPal-related field names")
    print("• iDEAL QR: 'qr' in payload or explicit 'idealqr' reference")
    print("• Explicit: 'payment_method', 'method', or 'service' fields")
    print("=" * 60)


if __name__ == "__main__":
    main()