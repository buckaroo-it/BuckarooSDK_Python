#!/usr/bin/env python3
"""
Unified Payment API Demo

This demo shows how to use the unified app.payments.create({payload}) API
where operations are automatically detected from the payload content.
"""

import os
import sys

# Add parent directory to Python path to import buckaroo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buckaroo.app import Buckaroo


def demo_unified_payment_api():
    """Demonstrate the unified payment API with operation detection."""
    
    print("UNIFIED PAYMENT API DEMO")
    print("=" * 50)
    
    # Setup app
    app = Buckaroo()
    app.log_info("Unified payment API demo started")
    
    print("\n1. Regular Payment (auto-detected by payment fields):")
    print("-" * 60)
    
    try:
        # Regular payment - detected automatically
        payment = app.payments.create({
            "amount": 25.50,
            "currency": "EUR",
            "description": "Product purchase",
            "invoice": "INV-001",
            "return_url": "https://www.buckaroo.nl",
            "return_url_cancel": "https://www.buckaroo.nl/cancel",
            "return_url_error": "https://www.buckaroo.nl/error",
            "return_url_reject": "https://www.buckaroo.nl/reject",
            "issuer": "ABNANL2A"  # This triggers iDEAL detection
        })
        
        print(f"✅ Created payment: {type(payment).__name__}")
        print(f"   Operation type: {payment._operation_type}")
        
        # Execute with unified API
        # response = payment.pay()  # Executes payment
        print("✅ Ready to execute payment with .pay()")
        
        # Simulate successful payment for next examples
        demo_transaction_key = "TXN_ABC123_PAYMENT"
        print(f"📝 Demo transaction key: {demo_transaction_key}")
        
    except Exception as e:
        print(f"❌ Payment Error: {e}")
        app.log_exception(e)
        return
    
    print("\n2. Refund (auto-detected by 'original_transaction_key'):")
    print("-" * 60)
    
    try:
        # Refund - detected by original_transaction_key in payload
        refund = app.payments.create({
            "original_transaction_key": demo_transaction_key,
            "refund_amount": 15.75,  # Partial refund
            "currency": "EUR",
            "description": "Partial refund for defective item",
            "invoice": "REF-001"
        })
        
        print(f"✅ Created refund: {type(refund).__name__}")
        print(f"   Operation type: {refund._operation_type}")
        print(f"   Original key: {refund._original_transaction_key}")
        print(f"   Refund amount: €{refund._operation_amount}")
        
        # Execute refund with unified API
        # response = refund.pay()  # Executes refund
        print("✅ Ready to execute refund with .pay()")
        
    except Exception as e:
        print(f"❌ Refund Error: {e}")
        app.log_exception(e)
    
    print("\n3. Capture (auto-detected by 'authorization_key'):")
    print("-" * 55)
    
    try:
        # Capture - detected by authorization_key in payload
        capture = app.payments.create({
            "authorization_key": "AUTH_DEF456_PENDING",
            "capture_amount": 20.00,  # Partial capture
            "currency": "USD",
            "description": "Capture partial authorization",
            "invoice": "CAP-001"
        })
        
        print(f"✅ Created capture: {type(capture).__name__}")
        print(f"   Operation type: {capture._operation_type}")
        print(f"   Authorization key: {capture._original_transaction_key}")
        print(f"   Capture amount: ${capture._operation_amount}")
        
        # response = capture.pay()  # Executes capture
        print("✅ Ready to execute capture with .pay()")
        
    except Exception as e:
        print(f"❌ Capture Error: {e}")
        app.log_exception(e)


def main():
    """Run all unified API demos."""
    
    print("BUCKAROO SDK - UNIFIED PAYMENT API DEMOS")
    print("=" * 65)
    
    print("\n📋 Operation Detection Rules:")
    print("✅ Payment: Default operation (amount, currency, payment method)")
    print("✅ Refund: 'original_transaction_key' or 'operation': 'refund'")
    print("✅ Capture: 'authorization_key' or 'action': 'capture'")
    print("✅ Cancel: 'cancel_key' or 'operation': 'cancel'")
    
    demo_unified_payment_api()
    
    print("\n" + "=" * 65)
    print("🎉 UNIFIED PAYMENT API DEMO COMPLETED!")
    print("\nKey Benefits:")
    print("• Single API: app.payments.create({payload}) for all operations")
    print("• Auto-detection: Operations determined from payload content")
    print("• Consistent: Same .pay() method executes any operation")
    print("• Intuitive: Operation context embedded in payload")
    print("=" * 65)


if __name__ == "__main__":
    main()