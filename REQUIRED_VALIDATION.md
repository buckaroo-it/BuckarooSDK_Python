# Required Parameter Validation

This document explains the required parameter validation feature implemented for the Buckaroo SDK.

## Overview

The validation system now supports **required parameter checking** that throws exceptions when mandatory parameters are missing. This ensures that payment requests cannot be built without essential service-specific parameters.

## Key Features

### 1. Exception-Based Validation
- **RequiredParameterMissingError**: Thrown when a required parameter is missing
- **ParameterValidationError**: Thrown for other validation issues (type mismatches, invalid parameters)

### 2. Flexible Validation Modes
- **Strict Validation** (`strict_validation=True`): Throws exceptions for validation errors
- **Non-Strict Validation** (`strict_validation=False`): Filters invalid parameters but still enforces required ones

### 3. Parameter Configuration
Each payment method defines parameters with metadata:
```python
{
    "VoucherCode": {
        "type": str, 
        "required": True, 
        "description": "The voucher code to use for the payment"
    }
}
```

## Usage Examples

### Basic Usage with Required Parameters

```python
from buckaroo.builders.payments.buckaroo_voucher_builder import BuckarooVoucherBuilder
from buckaroo.exceptions._parameter_validation_error import RequiredParameterMissingError

builder = BuckarooVoucherBuilder(client)
builder.currency("EUR").amount(10.00)  # ... other required fields

try:
    # This will throw RequiredParameterMissingError
    payment_request = builder.build(action="Pay", strict_validation=True)
except RequiredParameterMissingError as e:
    print(f"Missing required parameter: {e.parameter_name}")
    # Add the required parameter
    builder.add_parameter("VoucherCode", "VOUCHER123")
    # Now it will succeed
    payment_request = builder.build(action="Pay", strict_validation=True)
```

### Validation Modes

```python
# Strict validation - throws exceptions
try:
    payment_request = builder.build(action="Pay", validate=True, strict_validation=True)
except RequiredParameterMissingError as e:
    print(f"Required parameter missing: {e.parameter_name}")

# Non-strict validation - filters invalid but still checks required
try:
    payment_request = builder.build(action="Pay", validate=True, strict_validation=False)
except RequiredParameterMissingError as e:
    print(f"Required parameter missing: {e.parameter_name}")

# No validation - skip all parameter validation
payment_request = builder.build(action="Pay", validate=False)
```

## Exception Details

### RequiredParameterMissingError
- `parameter_name`: Name of the missing parameter
- `action`: Action being performed (e.g., "Pay", "PayEncrypted")
- `service_name`: Name of the payment service

### ParameterValidationError
- `parameter_name`: Name of the invalid parameter
- `expected_type`: Expected parameter type
- `action`: Action being performed
- `service_name`: Name of the payment service

## Implementation Details

### ServiceParameterValidator Methods
- `validate_required_parameters()`: Checks all required parameters are present
- `validate_all_parameters()`: Validates all parameters with strict/non-strict modes
- `validate_parameter_type()`: Validates individual parameter types

### PaymentBuilder Integration
- `build()` method accepts `strict_validation` parameter
- `pay()`, `execute_action()` methods support strict validation
- All validation happens before request building

## Backward Compatibility

The feature is fully backward compatible:
- Default behavior remains unchanged (non-strict validation)
- Existing code continues to work without modification
- Strict validation is opt-in via `strict_validation=True`

## Payment Method Examples

### BuckarooVoucherBuilder
```python
# Required for Pay action:
- VoucherCode (string): The voucher code to use
```

### CreditcardBuilder
```python
# Most parameters are optional for basic Pay action
# Required parameters depend on specific action and configuration
```

## Best Practices

1. **Use strict validation in production** to catch configuration errors early
2. **Handle RequiredParameterMissingError** gracefully in your application
3. **Check parameter requirements** using `get_allowed_service_parameters(action)`
4. **Use case-insensitive parameter names** (voucher_code matches VoucherCode)

## Testing

Run the test files to see validation in action:
- `test_required_validation.py`: Demonstrates BuckarooVoucherBuilder validation
- `example_validation.py`: Shows CreditcardBuilder usage patterns

The validation system ensures robust parameter handling while maintaining flexibility for different payment scenarios.