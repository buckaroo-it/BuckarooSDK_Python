#!/usr/bin/env python3

"""
Test script to verify Alipay service structure output.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from buckaroo.builders.payments.alipay_builder import AlipayBuilder
from buckaroo.config.buckaroo_config import BuckarooConfig
from buckaroo._buckaroo_client import BuckarooClient


def test_alipay_structure():
    """Test the Alipay service structure generation."""
    print("Testing Alipay service structure...")
    
    # Create a mock client (we don't need real credentials for structure testing)
    config = BuckarooConfig("test_key", "test_secret", "test")
    client = BuckarooClient(config)
    
    # Create Alipay builder
    builder = AlipayBuilder(client)
    
    # Set basic payment details
    builder.currency("EUR") \
           .amount(0.01) \
           .invoice("testinvoice 1234") \
           .use_mobile_view(True)
    
    # Build the payment request
    payment_request = builder.build()
    
    # Convert to dictionary to see the structure
    request_dict = payment_request.to_dict()
    
    print("Generated request structure:")
    import json
    print(json.dumps(request_dict, indent=2))
    
    # Check the Services structure specifically
    services = request_dict.get('Services', {})
    service_list = services.get('ServiceList', [])
    
    if service_list:
        service = service_list[0]
        print(f"\nService Name: {service.get('Name')}")
        print(f"Service Action: {service.get('Action')}")
        print(f"Parameters: {service.get('Parameters', [])}")
        
        # Verify the structure matches expected format
        expected_structure = service.get('Parameters') is not None
        print(f"\nStructure matches expected format: {expected_structure}")
        
        if expected_structure and service.get('Parameters'):
            for param in service.get('Parameters', []):
                print(f"Parameter: {param.get('Name')} = {param.get('Value')}")
    else:
        print("No services found in the request!")


if __name__ == "__main__":
    test_alipay_structure()