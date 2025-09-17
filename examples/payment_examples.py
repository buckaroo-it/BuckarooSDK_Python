"""
Example usage of the Buckaroo Payment System

This example demonstrates how to use the factory pattern and builder pattern
to create different types of payments.
"""

from buckaroo._buckaroo_client import BuckarooClient


def main():
    # Initialize the Buckaroo client
    client = BuckarooClient("your_store_key", "your_secret_key")
    
    # Example 1: Create an iDEAL payment using dictionary parameters (quick setup)
    print("=== iDEAL Payment Example (Dictionary Parameters) ===")
    
    ideal_payment_dict = client.payments.create_payment("ideal", {
        'currency': 'EUR',
        'amount': 6.0,
        'description': 'Automated test iDEAL with no issuer in the request',
        'invoice': 'Automatedtest_iDEAL_0013',
        'return_url': 'https://www.buckaroo.nl',
        'return_url_cancel': 'https://www.buckaroo.nl/annuleren',
        'return_url_error': 'https://www.buckaroo.nl/mislukt',
        'return_url_reject': 'https://www.buckaroo.nl/geweigerd',
        'continue_on_incomplete': '1',
        'client_ip': {'address': '0.0.0.0', 'type': 0}
    })
    
    # Execute the payment
    try:
        result = ideal_payment_dict.execute()
        print("Payment executed successfully:", result)
    except Exception as e:
        print("Payment failed:", e)
    
    # Example 1b: Create an iDEAL payment using fluent interface (original approach)
    print("\n=== iDEAL Payment Example (Fluent Interface) ===")
    
    ideal_payment_fluent = (client.payments.create_payment("ideal")
                           .currency("EUR")
                           .amount(6.0)
                           .description("Automated test iDEAL with no issuer in the request")
                           .invoice("Automatedtest_iDEAL_0013")
                           .return_url("https://www.buckaroo.nl")
                           .return_url_cancel("https://www.buckaroo.nl/annuleren")
                           .return_url_error("https://www.buckaroo.nl/mislukt")
                           .return_url_reject("https://www.buckaroo.nl/geweigerd")
                           .continue_on_incomplete("1")
                           .client_ip("0.0.0.0", 0))
    
    # Execute the payment
    try:
        result = ideal_payment_fluent.execute()
        print("Payment executed successfully:", result)
    except Exception as e:
        print("Payment failed:", e)
    
    # Example 1c: Combining both approaches (dictionary + fluent interface)
    print("\n=== iDEAL Payment Example (Combined Approach) ===")
    
    ideal_payment_combined = (client.payments.create_payment("ideal", {
        'currency': 'EUR',
        'amount': 6.0,
        'return_url': 'https://www.buckaroo.nl',
        'return_url_cancel': 'https://www.buckaroo.nl/annuleren',
        'return_url_error': 'https://www.buckaroo.nl/mislukt',
        'return_url_reject': 'https://www.buckaroo.nl/geweigerd'
    }).description("Combined approach payment")  # Override with fluent interface
      .invoice("COMBINED-001")  # Add additional parameters
      .client_ip("192.168.1.1", 1))  # Override client IP
    
    try:
        result = ideal_payment_combined.execute()
        print("Payment executed successfully:", result)
    except Exception as e:
        print("Payment failed:", e)
    
    # Example 2: Create a credit card payment using dictionary parameters
    print("\n=== Credit Card Payment Example (Dictionary Parameters) ===")
    
    cc_payment_dict = client.payments.create_payment("creditcard", {
        'currency': 'EUR',
        'amount': 25.50,
        'description': 'Credit card payment',
        'invoice': 'CC-001',
        'return_url': 'https://example.com/success',
        'return_url_cancel': 'https://example.com/cancel',
        'return_url_error': 'https://example.com/error',
        'return_url_reject': 'https://example.com/reject',
        'service_parameters': {
            'cardNumber': '4111111111111111',
            'expiryMonth': '12',
            'expiryYear': '2025',
            'cvv': '123'
        }
    })
    
    try:
        result = cc_payment_dict.execute()
        print("Payment executed successfully:", result)
    except Exception as e:
        print("Payment failed:", e)
    
    # Example 2b: Create a credit card payment using fluent interface
    print("\n=== Credit Card Payment Example (Fluent Interface) ===")
    
    cc_payment = (client.payments.create_payment("creditcard")
                  .currency("EUR")
                  .amount(25.50)
                  .description("Credit card payment")
                  .invoice("CC-001")
                  .return_url("https://example.com/success")
                  .return_url_cancel("https://example.com/cancel")
                  .return_url_error("https://example.com/error")
                  .return_url_reject("https://example.com/reject")
                  .card_number("4111111111111111")
                  .expiry_month("12")
                  .expiry_year("2025")
                  .cvv("123"))
    
    try:
        result = cc_payment.execute()
        print("Payment executed successfully:", result)
    except Exception as e:
        print("Payment failed:", e)
    
    # Example 3: Create a PayPal payment
    print("\n=== PayPal Payment Example ===")
    
    paypal_payment = (client.payments.create_payment("paypal")
                      .currency("EUR")
                      .amount(15.75)
                      .description("PayPal payment")
                      .invoice("PP-002")
                      .return_url("https://example.com/success")
                      .return_url_cancel("https://example.com/cancel")
                      .return_url_error("https://example.com/error")
                      .return_url_reject("https://example.com/reject"))
    
    try:
        result = paypal_payment.execute()
        print("Payment executed successfully:", result)
    except Exception as e:
        print("Payment failed:", e)
    
    # Example 4: Check available payment methods
    print("\n=== Available Payment Methods ===")
    available_methods = client.payments.get_available_methods()
    print("Available payment methods:", available_methods)
    
    # Example 5: Check if a method is supported
    print("\n=== Method Support Check ===")
    print("Is 'ideal' supported?", client.payments.is_method_supported("ideal"))
    print("Is 'bitcoin' supported?", client.payments.is_method_supported("bitcoin"))


if __name__ == "__main__":
    main()