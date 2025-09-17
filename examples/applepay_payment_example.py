"""
Example: Apple Pay Payment Method Usage

This example demonstrates how to use the Apple Pay payment method with the Buckaroo SDK.
Apple Pay processes secure payments using encrypted payment data from iOS devices.
"""

from buckaroo._buckaroo_client import BuckarooClient
from datetime import datetime


def main():
    # Initialize the Buckaroo client
    client = BuckarooClient("your_store_key", "your_secret_key")
    
    print("=== Apple Pay Payment Examples ===\n")
    
    # Sample Apple Pay payment data (in real usage, this comes from the Apple Pay framework)
    sample_payment_data = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcHBsZXBheSJ9.sample_encrypted_data"
    
    # Example 1: Basic Apple Pay payment using fluent interface
    print("1. Basic Apple Pay Payment (Fluent Interface):")
    
    basic_payment = (client.payments.create_payment("applepay")
                    .payment_data(sample_payment_data)
                    .customer_card_name("John Doe")
                    .currency("EUR")
                    .amount_debit(25.99)
                    .invoice(f"APPLE_PAY_{int(datetime.now().timestamp())}"))
    
    print("   Payment Request JSON:")
    result = basic_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 2: Apple Pay payment using dictionary parameters
    print("2. Apple Pay Payment (Dictionary Parameters):")
    
    apple_pay_params = {
        'payment_data': sample_payment_data,
        'customer_card_name': 'Jane Smith',
        'currency': 'USD',
        'amount_debit': 49.99,
        'invoice': f'DICT_APPLE_{int(datetime.now().timestamp())}',
        'description': 'Premium app purchase'
    }
    
    dict_payment = client.payments.create_payment("applepay", apple_pay_params)
    
    print("   Payment Request JSON:")
    result = dict_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 3: Apple Pay with service_parameters structure
    print("3. Apple Pay with Service Parameters:")
    
    service_params = {
        'currency': 'EUR',
        'amount_debit': 15.50,
        'invoice': f'SERVICE_APPLE_{int(datetime.now().timestamp())}',
        'service_parameters': {
            'PaymentData': sample_payment_data,
            'CustomerCardName': 'Alice Johnson',
            'TransactionId': 'TXN-12345',
            'MerchantReference': 'REF-67890'
        }
    }
    
    service_payment = client.payments.create_payment("applepay", service_params)
    
    print("   Payment Request JSON:")
    result = service_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 4: Combined dictionary and fluent interface
    print("4. Combined Dictionary + Fluent Interface:")
    
    base_params = {
        'payment_data': sample_payment_data,
        'currency': 'GBP',
        'amount_debit': 35.00
    }
    
    combined_payment = (client.payments.create_payment("applepay", base_params)
                       .customer_card_name("Bob Wilson")  # Add via fluent
                       .invoice("COMBO-APPLE-001")  # Add via fluent
                       .description("Combined payment example"))  # Add via fluent
    
    print("   Payment Request JSON:")
    result = combined_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 5: Apple Pay with custom parameters
    print("5. Apple Pay with Custom Parameters:")
    
    custom_payment = (client.payments.create_payment("applepay")
                     .payment_data(sample_payment_data)
                     .customer_card_name("Charlie Brown")
                     .currency("EUR")
                     .amount_debit(12.75)
                     .invoice("CUSTOM-APPLE-001"))
    
    # Add custom parameters for advanced features
    custom_payment.add_apple_pay_parameter("DeviceIdentifier", "iPhone-12-Pro")
    custom_payment.add_apple_pay_parameter("AppVersion", "2.1.0")
    custom_payment.add_apple_pay_parameter("LocationData", "Amsterdam, NL", "Location", "Store1")
    
    print("   Payment Request JSON:")
    result = custom_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 6: Minimal Apple Pay payment (only required fields)
    print("6. Minimal Apple Pay Payment:")
    
    minimal_payment = (client.payments.create_payment("applepay")
                      .payment_data(sample_payment_data)
                      .currency("EUR")
                      .amount_debit(5.00))
    
    print("   Payment Request JSON:")
    result = minimal_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 7: Demonstration of execution (mock)
    print("7. Payment Execution Example:")
    
    execution_payment = (client.payments.create_payment("applepay")
                        .payment_data(sample_payment_data)
                        .customer_card_name("Demo User")
                        .currency("EUR")
                        .amount_debit(10.00)
                        .invoice(f"EXEC_APPLE_{int(datetime.now().timestamp())}"))
    
    try:
        # This would normally send the request to Buckaroo
        result = execution_payment.execute()
        print(f"   Execution result: {result}")
    except Exception as e:
        print(f"   Execution would send request to Buckaroo API")
        print(f"   (In this example: {e})")
    
    # Example 8: Real-world e-commerce scenario
    print("\n8. E-commerce Purchase Scenario:")
    
    ecommerce_payment = (client.payments.create_payment("applepay")
                        .payment_data(sample_payment_data)
                        .customer_card_name("Sarah Connor")
                        .currency("EUR")
                        .amount_debit(129.99)
                        .invoice("ORDER-2025-0917-001")
                        .description("MacBook Pro 14-inch purchase")
                        .return_url("https://mystore.com/payment/success")
                        .return_url_cancel("https://mystore.com/payment/cancel")
                        .return_url_error("https://mystore.com/payment/error")
                        .return_url_reject("https://mystore.com/payment/reject"))
    
    # Add e-commerce specific parameters
    ecommerce_payment.add_apple_pay_parameter("OrderNumber", "ORD-2025-001")
    ecommerce_payment.add_apple_pay_parameter("CustomerEmail", "sarah@example.com")
    ecommerce_payment.add_apple_pay_parameter("ShippingMethod", "express")
    
    print("   E-commerce Payment Request JSON:")
    result = ecommerce_payment.build()
    print(f"   {result.to_json()}\n")
    
    print("=== Apple Pay Integration Tips ===")
    print("• Apple Pay requires encrypted payment data from the Apple Pay framework")
    print("• PaymentData is mandatory - obtained from PKPayment.token")
    print("• CustomerCardName is optional but recommended for better UX")
    print("• Use 'Pay' action for immediate payment processing")
    print("• Apple Pay supports immediate payment without redirect")
    print("• Ensure your app has Apple Pay entitlements configured")
    print("• Test with Apple Pay sandbox environment first")
    print("• Handle Apple Pay authentication failures gracefully")
    print("• Consider implementing Apple Pay on both iOS app and web")
    print("• PaymentData contains sensitive encrypted information")
    
    print("\n=== Apple Pay Implementation Flow ===")
    print("1. Configure Apple Pay in your iOS app or web page")
    print("2. Present Apple Pay button to user")
    print("3. User authenticates with Face ID/Touch ID/Passcode")
    print("4. Receive PKPayment with encrypted token")
    print("5. Extract payment data from PKPayment.token")
    print("6. Send payment data to your backend")
    print("7. Create Buckaroo Apple Pay payment with payment data")
    print("8. Process payment through Buckaroo API")
    print("9. Handle payment result and update order status")


if __name__ == "__main__":
    main()