#!/usr/bin/env python3
"""
Test script demonstrating required parameter validation for BuckarooVoucherBuilder.
"""

import sys
import os

# Add the parent directory to the path so we can import buckaroo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from buckaroo.builders.payments.buckaroo_voucher_builder import BuckarooVoucherBuilder
from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError, ParameterValidationError

class MockClient:
    """Mock client for testing."""
    pass

def test_required_parameter_validation():
    """Test that required parameter validation works correctly."""
    
    print("=== Testing Required Parameter Validation for BuckarooVoucherBuilder ===\n")
    
    # Create a mock client and voucher builder
    client = MockClient()
    builder = BuckarooVoucherBuilder(client)
    
    # Set up basic payment information
    builder.currency("EUR") \
           .amount(10.00) \
           .description("Test voucher payment") \
           .invoice("INV-001") \
           .return_url("https://example.com/success") \
           .return_url_cancel("https://example.com/cancel") \
           .return_url_error("https://example.com/error") \
           .return_url_reject("https://example.com/reject")
    
    print("1. Testing with missing required parameter (VoucherCode)...\n")
    
    try:
        # Try to build without the required VoucherCode parameter
        # Use strict_validation=True to enforce required parameter checking
        payment_request = builder.build(action="Pay", validate=True, strict_validation=True)
        print("❌ ERROR: Should have thrown RequiredParameterMissingError")
    except RequiredParameterMissingError as e:
        print("✅ SUCCESS: Caught RequiredParameterMissingError as expected")
        print(f"   Error message: {e}")
        print(f"   Parameter name: {e.parameter_name}")
        print(f"   Action: {e.action}")
        print(f"   Service name: {e.service_name}\n")
    except Exception as e:
        print(f"❌ ERROR: Unexpected exception type: {type(e).__name__}: {e}\n")
    
    print("2. Testing with required parameter provided...\n")
    
    try:
        # Add the required VoucherCode parameter
        builder.add_parameter("VoucherCode", "VOUCHER123")
        
        # Now build should succeed
        payment_request = builder.build(action="Pay", validate=True, strict_validation=True)
        print("✅ SUCCESS: Payment request built successfully with required parameter")
        print(f"   Service name: {payment_request.services.services[0].name}")
        print(f"   Action: {payment_request.services.services[0].action}")
        print(f"   Parameters: {[p.name + '=' + p.value for p in payment_request.services.services[0].parameters]}\n")
    except Exception as e:
        print(f"❌ ERROR: Unexpected exception: {type(e).__name__}: {e}\n")
    
    print("3. Testing parameter case insensitivity and underscore tolerance...\n")
    
    try:
        # Create a new builder
        builder2 = BuckarooVoucherBuilder(client)
        builder2.currency("EUR") \
                .amount(10.00) \
                .description("Test voucher payment") \
                .invoice("INV-002") \
                .return_url("https://example.com/success") \
                .return_url_cancel("https://example.com/cancel") \
                .return_url_error("https://example.com/error") \
                .return_url_reject("https://example.com/reject")
        
        # Add parameter with different case and underscores
        builder2.add_parameter("voucher_code", "VOUCHER456")  # Should match "VoucherCode"
        
        payment_request = builder2.build(action="Pay", validate=True, strict_validation=True)
        print("✅ SUCCESS: Case insensitive and underscore tolerant parameter matching works")
        print("   Original parameter: voucher_code")
        print("   Matched parameter: VoucherCode")
        print(f"   Value: {payment_request.services.services[0].parameters[0].value}\n")
    except Exception as e:
        print(f"❌ ERROR: Case insensitive matching failed: {type(e).__name__}: {e}\n")
    
    print("=== Test completed ===")

if __name__ == "__main__":
    test_required_parameter_validation()