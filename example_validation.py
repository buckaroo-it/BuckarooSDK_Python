"""
Example showing required parameter validation usage with CreditCard builder.
"""

from buckaroo.builders.payments.credit_card_builder import CreditcardBuilder
from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError, ParameterValidationError

# Mock client for demonstration
class MockClient:
    pass

def example_usage():
    """Example showing how to use required parameter validation."""
    
    print("=== Example: Required Parameter Validation ===\n")
    
    client = MockClient()
    builder = CreditcardBuilder(client)
    
    # Set up basic payment details
    builder.currency("EUR") \
           .amount(25.00) \
           .description("Online purchase") \
           .invoice("INV-12345") \
           .return_url("https://shop.example.com/success") \
           .return_url_cancel("https://shop.example.com/cancel") \
           .return_url_error("https://shop.example.com/error") \
           .return_url_reject("https://shop.example.com/reject")
    
    # Example 1: Using strict validation (throws exceptions for missing required params)
    print("Example 1: Strict validation with missing required parameter")
    try:
        # For PayEncrypted action, let's check what parameters are required
        allowed_params = builder.get_allowed_service_parameters("PayEncrypted")
        required_params = [name for name, config in allowed_params.items() if config.get('required', False)]
        print(f"Required parameters for PayEncrypted: {required_params}")
        
        # Try to build without required parameters
        payment_request = builder.build(action="PayEncrypted", validate=True, strict_validation=True)
        print("✅ Build succeeded (no required parameters for this action)")
        
    except RequiredParameterMissingError as e:
        print(f"❌ Missing required parameter: {e.parameter_name}")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Other error: {type(e).__name__}: {e}")
    
    print()
    
    # Example 2: Adding required parameters and succeeding
    print("Example 2: Adding parameters and validating")
    try:
        # Add some service parameters (these are optional for CreditCard Pay)
        builder.add_parameter("SaveToken", "true")
        builder.add_parameter("TokenKey", "abc123")
        
        # Build with validation
        payment_request = builder.build(action="Pay", validate=True, strict_validation=True)
        print("✅ Payment request built successfully")
        print(f"   Service: {payment_request.services.services[0].name}")
        print(f"   Action: {payment_request.services.services[0].action}")
        if payment_request.services.services[0].parameters:
            params = [f"{p.name}={p.value}" for p in payment_request.services.services[0].parameters]
            print(f"   Parameters: {params}")
        
    except (RequiredParameterMissingError, ParameterValidationError) as e:
        print(f"❌ Validation error: {e}")
    except Exception as e:
        print(f"❌ Other error: {type(e).__name__}: {e}")
    
    print()
    
    # Example 3: Non-strict validation (filters invalid params, but still checks required)
    print("Example 3: Non-strict validation")
    try:
        # Add an invalid parameter
        builder.add_parameter("InvalidParam", "should_be_filtered")
        
        # Non-strict validation will filter invalid params but still check required ones
        payment_request = builder.build(action="Pay", validate=True, strict_validation=False)
        print("✅ Payment request built with non-strict validation")
        if payment_request.services.services[0].parameters:
            params = [f"{p.name}={p.value}" for p in payment_request.services.services[0].parameters]
            print(f"   Valid parameters kept: {params}")
        
    except RequiredParameterMissingError as e:
        print(f"❌ Still missing required parameter: {e.parameter_name}")
    except Exception as e:
        print(f"❌ Other error: {type(e).__name__}: {e}")
    
    print("\n=== Example completed ===")

if __name__ == "__main__":
    example_usage()