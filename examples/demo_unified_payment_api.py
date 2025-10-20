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
    
    print("\n3. Full Refund (no amount specified):")
    print("-" * 45)
    
    try:
        # Full refund - no refund_amount means full refund
        full_refund = app.payments.create({
            "original_transaction_key": demo_transaction_key,
            "currency": "EUR",
            "description": "Full refund - customer return",
            "invoice": "FULLREF-001"
        })
        
        print(f"✅ Created full refund: {type(full_refund).__name__}")
        print(f"   Operation type: {full_refund._operation_type}")
        print("   Refund amount: Full amount (not specified)")
        
        # response = full_refund.pay()  # Executes full refund
        print("✅ Ready to execute full refund with .pay()")
        
    except Exception as e:
        print(f"❌ Full Refund Error: {e}")
        app.log_exception(e)
    
    print("\n4. Capture (auto-detected by 'authorization_key'):")
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
    
    print("\n5. Cancel (auto-detected by 'cancel_key'):")
    print("-" * 45)
    
    try:
        # Cancel - detected by cancel_key in payload
        cancel = app.payments.create({
            "cancel_key": "PENDING_GHI789_CANCEL",
            "description": "Cancel pending payment - customer request",
            "invoice": "CANCEL-001"
        })
        
        print(f"✅ Created cancellation: {type(cancel).__name__}")
        print(f"   Operation type: {cancel._operation_type}")
        print(f"   Cancel key: {cancel._original_transaction_key}")
        
        # response = cancel.pay()  # Executes cancellation
        print("✅ Ready to execute cancellation with .pay()")
        
    except Exception as e:
        print(f"❌ Cancel Error: {e}")
        app.log_exception(e)


def demo_explicit_operations():
    """Demonstrate explicit operation specification."""
    
    print("\n" + "=" * 50)
    print("EXPLICIT OPERATION DEMO")
    print("=" * 50)
    
    app = Buckaroo()
    
    print("\n6. Explicit Operation Types:")
    print("-" * 35)
    
    try:
        # Explicit refund using 'operation' field
        explicit_refund = app.payments.create({
            "operation": "refund",
            "original_transaction_key": "TXN_EXPLICIT_123",
            "refund_amount": 30.00,
            "currency": "EUR",
            "description": "Explicit refund operation"
        })
        
        print(f"✅ Explicit refund: {explicit_refund._operation_type}")
        
        # Explicit capture using 'action' field
        explicit_capture = app.payments.create({
            "action": "capture",
            "authorization_key": "AUTH_EXPLICIT_456",
            "capture_amount": 45.00,
            "currency": "USD",
            "description": "Explicit capture operation"
        })
        
        print(f"✅ Explicit capture: {explicit_capture._operation_type}")
        
    except Exception as e:
        print(f"❌ Explicit Operations Error: {e}")
        app.log_exception(e)


def demo_mixed_scenarios():
    """Demonstrate mixed and complex scenarios."""
    
    print("\n" + "=" * 50)
    print("MIXED SCENARIOS DEMO")
    print("=" * 50)
    
    app = Buckaroo()
    
    print("\n7. Different Payment Methods with Operations:")
    print("-" * 50)
    
    try:
        # Credit card refund
        cc_refund = app.payments.create({
            "original_transaction_key": "CC_TXN_789",
            "refund_amount": 50.00,
            "currency": "USD",
            "description": "Credit card refund",
            "card_number": "4111111111111111"  # Indicates credit card method
        })
        
        print(f"✅ Credit card refund: {type(cc_refund).__name__}")
        print(f"   Operation: {cc_refund._operation_type}")
        
        # PayPal capture
        paypal_capture = app.payments.create({
            "payment_method": "paypal",  # Explicit method
            "authorization_key": "PAYPAL_AUTH_456",
            "capture_amount": 75.00,
            "currency": "EUR",
            "description": "PayPal authorization capture"
        })
        
        print(f"✅ PayPal capture: {type(paypal_capture).__name__}")
        print(f"   Operation: {paypal_capture._operation_type}")
        
    except Exception as e:
        print(f"❌ Mixed Scenarios Error: {e}")
        app.log_exception(e)


def demo_error_handling():
    """Demonstrate error handling for the unified API."""
    
    print("\n" + "=" * 50)
    print("ERROR HANDLING DEMO")
    print("=" * 50)
    
    app = Buckaroo()
    
    print("\n8. Error Cases:")
    print("-" * 20)
    
    # Missing transaction key for refund
    try:
        invalid_refund = app.payments.create({
            "refund_amount": 10.00,
            "currency": "EUR",
            "description": "Invalid refund - no transaction key"
        })
        # This should work (creates builder) but fail on execution
        response = invalid_refund.pay()
    except ValueError as e:
        print(f"✅ Correctly caught missing transaction key: {e}")
    
    # Ambiguous payload
    try:
        ambiguous = app.payments.create({
            "amount": 10.00,
            "description": "Ambiguous payment - no method indicators"
        })
    except ValueError as e:
        print(f"✅ Correctly caught ambiguous payload: {e}")\n\n\ndef main():\n    \"\"\"Run all unified API demos.\"\"\"\n    \n    print(\"BUCKAROO SDK - UNIFIED PAYMENT API DEMOS\")\n    print(\"=\" * 65)\n    \n    print(\"\\n📋 Operation Detection Rules:\")\n    print(\"✅ Payment: Default operation (amount, currency, payment method)\")\n    print(\"✅ Refund: 'original_transaction_key' or 'operation': 'refund'\")\n    print(\"✅ Capture: 'authorization_key' or 'action': 'capture'\")\n    print(\"✅ Cancel: 'cancel_key' or 'operation': 'cancel'\")\n    print(\"✅ Explicit: 'operation' or 'action' field overrides auto-detection\")\n    \n    demo_unified_payment_api()\n    demo_explicit_operations()\n    demo_mixed_scenarios()\n    demo_error_handling()\n    \n    print(\"\\n\" + \"=\" * 65)\n    print(\"🎉 UNIFIED PAYMENT API DEMO COMPLETED!\")\n    print(\"\\nKey Benefits:\")\n    print(\"• Single API: app.payments.create({payload}) for all operations\")\n    print(\"• Auto-detection: Operations determined from payload content\")\n    print(\"• Consistent: Same .pay() method executes any operation\")\n    print(\"• Flexible: Explicit operation specification supported\")\n    print(\"• Intuitive: Operation context embedded in payload\")\n    print(\"=\" * 65)\n\n\nif __name__ == \"__main__\":\n    main()