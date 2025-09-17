"""
Example: HTTP Request Implementation

This example demonstrates how the Buckaroo SDK now handles HTTP requests
with HMAC authentication, retry logic, and comprehensive error handling.
"""

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.config.buckaroo_config import BuckarooConfig, Environment, ConfigBuilder
from buckaroo.http.client import BuckarooApiError
from buckaroo.exceptions._authentication_error import AuthenticationError


def main():
    print("=== Buckaroo HTTP Request Examples ===\n")
    
    # Example 1: Basic payment execution with HTTP requests
    print("1. Basic Payment Execution:")
    
    try:
        client = BuckarooClient("test_store_key", "test_secret_key", mode="test")
        
        # Create an iDEAL payment
        payment = (client.payments.create_payment("ideal")
                  .currency("EUR")
                  .amount_debit(25.00)
                  .description("Test payment")
                  .invoice("INV-001")
                  .issuer("ABNANL2A")
                  .return_url("https://example.com/success")
                  .return_url_cancel("https://example.com/cancel")
                  .return_url_error("https://example.com/error")
                  .return_url_reject("https://example.com/reject"))
        
        print("   Creating payment request...")
        print(f"   Request data: {payment.build().to_json()}")
        
        # Execute the payment (this will make actual HTTP request)
        print("   Executing payment...")
        result = payment.execute()
        
        print(f"   Response: {result}")
        
    except AuthenticationError as e:
        print(f"   Authentication Error: {e}")
    except BuckarooApiError as e:
        print(f"   API Error: {e}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Example 2: Payment execution with custom configuration
    print("2. Payment with Custom HTTP Configuration:")
    
    try:
        # Create custom config with longer timeout and more retries
        config = (ConfigBuilder()
                 .test_environment()
                 .timeout(60)
                 .retry_attempts(5)
                 .retry_delay(2.0)
                 .enable_logging()
                 .build())
        
        client = BuckarooClient("store_key", "secret_key", config=config)
        
        print(f"   HTTP Client Config: {client.get_config_info()}")
        print(f"   API Endpoint: {client.api_endpoint}")
        
        # Create Apple Pay payment
        apple_pay_payment = (client.payments.create_payment("applepay")
                           .payment_data("encrypted_apple_pay_token")
                           .customer_card_name("John Doe")
                           .currency("EUR")
                           .amount_debit(49.99)
                           .invoice("APPLE-001")
                           .description("Apple Pay purchase"))
        
        print("   Creating Apple Pay payment...")
        result = apple_pay_payment.execute()
        print(f"   Result: {result}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Example 3: HTTP response handling
    print("3. HTTP Response Handling:")
    
    try:
        client = BuckarooClient("test_key", "test_secret")
        
        # Create IdealQr payment
        qr_payment = (client.payments.create_payment("idealqr")
                     .description("QR Code payment")
                     .purchase_id("QR-001")
                     .amount(15.00)
                     .currency("EUR")
                     .invoice("QR-INV-001"))
        
        print("   Executing QR payment...")
        response = qr_payment.execute()
        
        # Access response properties
        print(f"   HTTP Status: {response.get('status_code', 'Unknown')}")
        print(f"   Success: {response.get('success', False)}")
        print(f"   Payment Key: {response.get('payment_key', 'N/A')}")
        print(f"   Transaction Key: {response.get('transaction_key', 'N/A')}")
        print(f"   Buckaroo Status: {response.get('buckaroo_status_code', 'N/A')}")
        print(f"   Status Message: {response.get('buckaroo_status_message', 'N/A')}")
        print(f"   Redirect URL: {response.get('redirect_url', 'N/A')}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Example 4: Error handling demonstration
    print("4. Error Handling Examples:")
    
    # Authentication error example
    print("   a) Authentication Error:")
    try:
        bad_client = BuckarooClient("invalid_key", "invalid_secret")
        payment = (bad_client.payments.create_payment("ideal")
                  .currency("EUR")
                  .amount_debit(10.00)
                  .description("Test")
                  .invoice("TEST-001")
                  .issuer("ABNANL2A")
                  .return_url("https://example.com/return")
                  .return_url_cancel("https://example.com/cancel")
                  .return_url_error("https://example.com/error")
                  .return_url_reject("https://example.com/reject"))
        
        result = payment.execute()
        print(f"      Unexpected success: {result}")
        
    except AuthenticationError as e:
        print(f"      Expected authentication error: {e}")
    except Exception as e:
        print(f"      Other error: {e}")
    
    # API error example
    print("   b) API Error (simulated):")
    try:
        client = BuckarooClient("test_key", "test_secret")
        
        # Create payment with invalid data to trigger API error
        invalid_payment = (client.payments.create_payment("ideal")
                          .currency("INVALID")  # Invalid currency
                          .amount_debit(-10.00)  # Invalid amount
                          .description("")  # Empty description
                          .invoice("")  # Empty invoice
                          .issuer("INVALID")  # Invalid issuer
                          .return_url("invalid-url")  # Invalid URL
                          .return_url_cancel("invalid-url")
                          .return_url_error("invalid-url")
                          .return_url_reject("invalid-url"))
        
        result = invalid_payment.execute()
        print(f"      Unexpected success: {result}")
        
    except BuckarooApiError as e:
        print(f"      Expected API error: {e}")
    except Exception as e:
        print(f"      Other error: {e}")
    
    print()
    
    # Example 5: HMAC authentication demonstration
    print("5. HMAC Authentication:")
    
    try:
        client = BuckarooClient("demo_store_key", "demo_secret_key")
        
        # Access the HTTP client directly for demonstration
        http_client = client.http_client
        
        print("   HMAC Authentication Details:")
        print(f"   Store Key: {http_client.store_key}")
        print(f"   API Endpoint: {http_client.config.api_endpoint}")
        
        # Generate sample authentication headers
        sample_headers = http_client._generate_hmac_signature(
            "POST",
            "https://testcheckout.buckaroo.nl/json/Transaction",
            '{"test":"data"}',
            "1234567890"
        )
        
        print("   Sample Authentication Headers:")
        for key, value in sample_headers.items():
            if key == "Authorization":
                # Mask the signature for security
                auth_parts = value.split(":")
                if len(auth_parts) >= 3:
                    masked_signature = auth_parts[1][:8] + "..." + auth_parts[1][-8:]
                    masked_value = f"{auth_parts[0]}:{masked_signature}:{auth_parts[2]}"
                    print(f"   {key}: {masked_value}")
                else:
                    print(f"   {key}: {value}")
            else:
                print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    print("=== HTTP Implementation Features ===")
    print("• HMAC SHA-256 authentication with timestamp")
    print("• Automatic retry logic with configurable attempts and delays")
    print("• Comprehensive error handling (auth, network, API errors)")
    print("• Response parsing with Buckaroo-specific status detection")
    print("• SSL verification and custom endpoint support")
    print("• Request/response logging capabilities")
    print("• Timeout configuration and connection pooling")
    print("• Automatic JSON serialization/deserialization")
    print("• Payment key and transaction key extraction")
    print("• Redirect URL detection for payment flows")
    
    print("\n=== Integration Benefits ===")
    print("• Payment builders now execute real API calls")
    print("• Unified error handling across all payment methods")
    print("• Configurable HTTP behavior through BuckarooConfig")
    print("• Production-ready authentication and security")
    print("• Comprehensive response data access")
    print("• Built-in retry logic for reliability")


if __name__ == "__main__":
    main()