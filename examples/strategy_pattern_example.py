"""
HTTP Strategy Pattern Example for Buckaroo SDK.

This example demonstrates how to use different HTTP strategies with the Buckaroo SDK.
"""

from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.http.strategies import HttpStrategyFactory


def demo_strategy_selection():
    """Demonstrate automatic strategy selection."""
    print("=== HTTP Strategy Selection Demo ===")
    
    # Check available strategies
    available_strategies = HttpStrategyFactory.get_available_strategies()
    print(f"Available HTTP strategies: {available_strategies}")
    
    # Check specific strategies
    print(f"Requests available: {HttpStrategyFactory.is_strategy_available('requests')}")
    print(f"Curl available: {HttpStrategyFactory.is_strategy_available('curl')}")


def demo_explicit_strategy():
    """Demonstrate using explicit HTTP strategies."""
    print("\n=== Explicit Strategy Demo ===")
    
    store_key = "IBjihN7Fhp"
    secret_key = "AB6176482E7B44C3BA7DB47F156088B5"
    
    try:
        # Try to use requests strategy explicitly
        print("\\nTrying requests strategy...")
        client_requests = BuckarooClient(
            store_key, 
            secret_key, 
            mode="test",
            http_strategy="requests"
        )
        print(f"✅ Successfully created client with requests strategy")
        print(f"Strategy in use: {client_requests.http_client.http_strategy.get_name()}")
        
    except RuntimeError as e:
        print(f"❌ Requests strategy failed: {e}")
    
    try:
        # Try to use curl strategy explicitly
        print("\\nTrying curl strategy...")
        client_curl = BuckarooClient(
            store_key, 
            secret_key, 
            mode="test", 
            http_strategy="curl"
        )
        print(f"✅ Successfully created client with curl strategy")
        print(f"Strategy in use: {client_curl.http_client.http_strategy.get_name()}")
        
    except RuntimeError as e:
        print(f"❌ Curl strategy failed: {e}")


def demo_auto_strategy():
    """Demonstrate automatic strategy selection."""
    print("\\n=== Auto Strategy Demo ===")
    
    store_key = "IBjihN7Fhp"
    secret_key = "AB6176482E7B44C3BA7DB47F156088B5"
    
    try:
        # Let the SDK choose the best strategy automatically
        client = BuckarooClient(store_key, secret_key, mode="test")
        strategy_name = client.http_client.http_strategy.get_name()
        print(f"✅ Auto-selected strategy: {strategy_name}")
        
        return client
        
    except RuntimeError as e:
        print(f"❌ No HTTP strategy available: {e}")
        return None


def demo_payment_with_strategy(client):
    """Demonstrate making a payment with the selected strategy."""
    if not client:
        print("\\n❌ No client available for payment demo")
        return
    
    print(f"\\n=== Payment Demo with {client.http_client.http_strategy.get_name()} strategy ===")
    
    try:
        # Create an iDEAL payment
        ideal_payment = client.payments.ideal_payment()
        
        # Configure payment
        ideal_payment.currency("EUR") \
                    .amount(10.00) \
                    .description("Strategy Pattern Test Payment") \
                    .invoice("TEST-STRATEGY-001") \
                    .return_url("https://example.com/return") \
                    .return_url_cancel("https://example.com/cancel") \
                    .return_url_error("https://example.com/error") \
                    .return_url_reject("https://example.com/reject")
        
        # Execute payment
        print("Making payment request...")
        response = ideal_payment.execute()
        
        print(f"✅ Payment request successful!")
        print(f"Payment Key: {response.payment_key}")
        print(f"Status: {response.status.code.code} - {response.status.code.description}")
        
        if response.requires_action():
            print(f"Redirect URL: {response.get_redirect_url()}")
        
    except Exception as e:
        print(f"❌ Payment failed: {e}")


def main():
    """Run all demonstrations."""
    print("🚀 Buckaroo SDK HTTP Strategy Pattern Demo")
    print("=" * 50)
    
    # Show available strategies
    demo_strategy_selection()
    
    # Try explicit strategies
    demo_explicit_strategy()
    
    # Use auto strategy
    client = demo_auto_strategy()
    
    # Make a payment with the selected strategy
    demo_payment_with_strategy(client)
    
    print("\\n✨ Demo completed!")


if __name__ == "__main__":
    main()