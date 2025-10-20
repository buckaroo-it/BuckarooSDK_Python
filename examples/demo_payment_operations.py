#!/usr/bin/env python3
"""
Payment Operations Demo

This demo shows how to use the enhanced payment builder with common operations
like pay, refund, partial refund, capture, and cancel.
"""

import os
import sys

# Add parent directory to Python path to import buckaroo module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from buckaroo.app import Buckaroo


def demo_payment_operations():
    """Demonstrate various payment operations."""
    
    print("PAYMENT OPERATIONS DEMO")
    print("=" * 50)
    
    # Setup app
    app = Buckaroo()
    app.log_info("Payment operations demo started")
    
    print("\n1. Create and Execute Payment (using .pay()):")
    print("-" * 55)
    
    try:
        # Create payment using factory pattern
        payment = app.payments.create({
            "amount": 25.50,
            "currency": "EUR",
            "description": "Demo payment for operations",
            "invoice": "PAY-001",
            "return_url": "https://www.buckaroo.nl",
            "return_url_cancel": "https://www.buckaroo.nl/cancel",
            "return_url_error": "https://www.buckaroo.nl/error",
            "return_url_reject": "https://www.buckaroo.nl/reject",
            "issuer": "ABNANL2A"
        })
        
        print(f"✅ Created payment builder: {type(payment).__name__}")
        app.log_info("Payment created successfully")
        
        # Execute payment using .pay() method (alias for .execute())
        # response = payment.pay()
        # print(f"✅ Payment executed successfully")
        # app.log_info(f"Payment executed with key: {response.key}")
        
        # For demo purposes, simulate a transaction key
        demo_transaction_key = "ABC123DEF456GHI789"
        print(f"📝 Demo transaction key: {demo_transaction_key}")
        
    except Exception as e:
        print(f"❌ Payment Error: {e}")
        app.log_exception(e)
        return
    
    print("\n2. Full Refund Operation:")
    print("-" * 35)
    
    try:
        # Create refund using the same builder or a new one
        refund_payment = app.payments.create({
            "currency": "EUR",
            "description": "Full refund for PAY-001",
            "invoice": "REF-001"
        })
        
        # Execute full refund
        # refund_response = refund_payment.refund(demo_transaction_key)
        print(f"✅ Full refund builder ready for transaction: {demo_transaction_key}")
        app.log_info("Full refund prepared")
        
    except Exception as e:
        print(f"❌ Refund Error: {e}")
        app.log_exception(e)
    
    print("\n3. Partial Refund Operation:")
    print("-" * 40)
    
    try:
        # Create partial refund
        partial_refund_payment = app.payments.create({
            "currency": "EUR",
            "description": "Partial refund for PAY-001",
            "invoice": "PREF-001"
        })
        
        # Execute partial refund (refund only 10.00 out of 25.50)
        partial_amount = 10.00
        # partial_response = partial_refund_payment.partial_refund(demo_transaction_key, partial_amount)
        print(f"✅ Partial refund of €{partial_amount} ready for transaction: {demo_transaction_key}")
        app.log_info(f"Partial refund of {partial_amount} prepared")
        
    except Exception as e:
        print(f"❌ Partial Refund Error: {e}")
        app.log_exception(e)
    
    print("\n4. Capture Operation (for authorized payments):")
    print("-" * 55)
    
    try:
        # Create capture for a previously authorized payment
        capture_payment = app.payments.create({
            "currency": "EUR",
            "description": "Capture authorized payment",
            "invoice": "CAP-001"
        })
        
        # Capture the full authorized amount
        # capture_response = capture_payment.capture(demo_transaction_key)
        print(f"✅ Capture builder ready for authorized transaction: {demo_transaction_key}")
        app.log_info("Capture operation prepared")
        
        # Partial capture example
        capture_amount = 20.00
        # partial_capture_response = capture_payment.capture(demo_transaction_key, capture_amount)
        print(f"✅ Partial capture of €{capture_amount} ready")
        
    except Exception as e:
        print(f"❌ Capture Error: {e}")
        app.log_exception(e)
    
    print("\n5. Cancel Operation:")
    print("-" * 25)
    
    try:
        # Create cancellation
        cancel_payment = app.payments.create({
            "description": "Cancel pending payment",
            "invoice": "CAN-001"
        })
        
        # Cancel the transaction
        # cancel_response = cancel_payment.cancel(demo_transaction_key)
        print(f"✅ Cancellation builder ready for transaction: {demo_transaction_key}")
        app.log_info("Cancellation operation prepared")
        
    except Exception as e:
        print(f"❌ Cancel Error: {e}")
        app.log_exception(e)


def demo_chained_operations():
    """Demonstrate chained payment operations."""
    
    print("\n" + "=" * 50)
    print("CHAINED OPERATIONS DEMO")
    print("=" * 50)
    
    app = Buckaroo()
    
    print("\n6. Fluent Interface with Operations:")
    print("-" * 45)
    
    try:
        # Build payment with fluent interface
        payment = app.payments.create({}) \
            .amount(50.00) \
            .currency("EUR") \
            .description("Fluent payment demo") \
            .invoice("FLUENT-001") \
            .return_url("https://www.buckaroo.nl") \
            .add_parameter("issuer", "ABNANL2A")
        
        print("✅ Payment built using fluent interface")
        
        # Execute payment
        # response = payment.pay()
        print("✅ Ready to execute payment with .pay()")
        
        # Simulate transaction for refund demo
        demo_key = "FLUENT123DEMO456"
        
        # Create refund builder from same app
        refund_builder = app.payments.create({}) \
            .currency("EUR") \
            .description("Fluent refund demo") \
            .invoice("FLUENT-REF-001")
        
        # Execute partial refund
        # refund_response = refund_builder.partial_refund(demo_key, 25.00)
        print(f"✅ Ready to execute partial refund of €25.00 for {demo_key}")
        
    except Exception as e:
        print(f"❌ Chained Operations Error: {e}")
        app.log_exception(e)


def demo_error_handling():
    """Demonstrate error handling for payment operations."""
    
    print("\n" + "=" * 50)
    print("ERROR HANDLING DEMO")
    print("=" * 50)
    
    app = Buckaroo()
    
    print("\n7. Error Cases:")
    print("-" * 20)
    
    # Test missing transaction key
    try:
        payment = app.payments.create({"amount": 10.00, "currency": "EUR"})
        # This should raise an error
        payment.refund("")  # Empty transaction key
    except ValueError as e:
        print(f"✅ Correctly caught empty transaction key: {e}")
    
    # Test invalid partial refund amount
    try:
        payment = app.payments.create({"currency": "EUR"})
        payment.partial_refund("DEMO123", -5.00)  # Negative amount
    except ValueError as e:
        print(f"✅ Correctly caught negative refund amount: {e}")
    
    # Test missing capture transaction key
    try:
        payment = app.payments.create({"currency": "EUR"})
        payment.capture("")  # Empty transaction key
    except ValueError as e:
        print(f"✅ Correctly caught empty capture key: {e}")


def main():
    """Run all payment operations demos."""
    
    print("BUCKAROO SDK - PAYMENT OPERATIONS DEMOS")
    print("=" * 60)
    
    print("\n📋 Available Payment Operations:")
    print("✅ .pay() - Execute payment (alias for .execute())")
    print("✅ .refund(transaction_key, amount=None) - Full or partial refund")
    print("✅ .partial_refund(transaction_key, amount) - Explicit partial refund")
    print("✅ .capture(transaction_key, amount=None) - Capture authorized payment")
    print("✅ .cancel(transaction_key) - Cancel pending transaction")
    
    demo_payment_operations()
    demo_chained_operations()
    demo_error_handling()
    
    print("\n" + "=" * 60)
    print("🎉 PAYMENT OPERATIONS DEMO COMPLETED!")
    print("\nOperation Summary:")
    print("• All payment builders now support common operations")
    print("• Operations work with any payment method (iDEAL, Credit Card, etc.)")
    print("• Fluent interface supported: .amount(50).currency('EUR').pay()")
    print("• Comprehensive error handling for invalid operations")
    print("• Logging integration for all operations")
    print("=" * 60)


if __name__ == "__main__":
    main()