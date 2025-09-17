#!/usr/bin/env python3
"""
Enhanced demo script showing different ways to create payments:
1. Dictionary parameters (quick setup)
2. Fluent interface (method chaining)  
3. Combined approach (dictionary + fluent)
"""

import json
from buckaroo._buckaroo_client import BuckarooClient


def demo_ideal_payments():
    """Demonstrate different ways to create iDEAL payments."""
    client = BuckarooClient("IBjihN7Fhp", "AB6176482E7B44C3BA7DB47F156088B5", mode="test")
    
    print("=" * 60)
    print("iDEAL PAYMENT EXAMPLES")
    print("=" * 60)
    
    # Method 1: Dictionary parameters (fastest for complete setup)
    print("\n1. Dictionary Parameters Approach:")
    print("-" * 40)
    
    ideal = client.payments.create_payment("ideal", {
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
    })
    
    response = ideal.execute()  # Now makes actual HTTP request to Buckaroo API

    # Check payment status
    if response.is_pending():
        print(f"Payment is pending. Redirect URL: {response.get_redirect_url()}")
    elif response.is_successful():
        print(f"Payment successful! Transaction ID: {response.get_transaction_id()}")
    elif response.is_failed():
        print(f"Payment failed: {response.status.sub_code.description}")

    # Access specific data
    print(f"Payment Key: {response.payment_key}")
    print(f"Amount: {response.amount_debit} {response.currency}")
    print(f"Status Code: {response.status.code.code} - {response.status.code.description}")

    print("Payment executed successfully.")
    # payment_dict = ideal_dict.build().to_dict()
    # print("Generated payment JSON:")
    # print(json.dumps(payment_dict, indent=2))
    
    # # Method 2: Fluent interface (most readable)
    # print("\n2. Fluent Interface Approach:")
    # print("-" * 40)
    
    # ideal_fluent = (client.payments.create_payment("ideal")
    #                .currency("EUR")
    #                .amount(6.0)
    #                .description("Automated test iDEAL with no issuer in the request")
    #                .invoice("Automatedtest_iDEAL_0013")
    #                .return_url("https://www.buckaroo.nl")
    #                .return_url_cancel("https://www.buckaroo.nl/annuleren")
    #                .return_url_error("https://www.buckaroo.nl/mislukt")
    #                .return_url_reject("https://www.buckaroo.nl/geweigerd")
    #                .continue_on_incomplete("1")
    #                .client_ip("0.0.0.0", 0)
    #                .issuer("ABNANL2A"))
    
    # payment_fluent = ideal_fluent.build().to_dict()
    # print("Both approaches generate the same JSON:", payment_dict == payment_fluent)
    
    # # Method 3: Combined approach (flexible)
    # print("\n3. Combined Approach (Dictionary + Fluent):")
    # print("-" * 40)
    
    # ideal_combined = (client.payments.create_payment("ideal", {
    #     'currency': 'EUR',
    #     'amount': 6.0,
    #     'return_url': 'https://www.buckaroo.nl',
    #     'return_url_cancel': 'https://www.buckaroo.nl/annuleren',
    #     'return_url_error': 'https://www.buckaroo.nl/mislukt',
    #     'return_url_reject': 'https://www.buckaroo.nl/geweigerd'
    # }).description("Combined approach - Dictionary + Fluent")  # Override description
    #   .invoice("COMBINED-001")  # Add missing invoice
    #   .client_ip("192.168.1.1", 1)  # Override client IP
    #   .issuer("INGBNL2A"))  # Add iDEAL issuer
    
    # payment_combined = ideal_combined.build().to_dict()
    # print("Combined approach JSON:")
    # print(json.dumps(payment_combined, indent=2))

if __name__ == "__main__":
    print("BUCKAROO PAYMENT SYSTEM - ENHANCED DEMO")
    print("=" * 80)
    
    demo_ideal_payments()
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETED")
    print("=" * 80)