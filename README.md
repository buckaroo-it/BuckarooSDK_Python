# Buckaroo SDK Python

Python SDK for the Buckaroo payment gateway. Process payments with iDEAL, Apple Pay, Credit Cards, PayPal, and more through a simple and intuitive API.

## Features

- 🏦 **Multiple Payment Methods**: iDEAL, Apple Pay, Credit Cards, PayPal, iDEAL QR
- 🔐 **Secure Authentication**: HMAC SHA-256 authentication with automatic signing
- 🌐 **HTTP Client**: Built-in HTTP client with retry logic and error handling
- ⚙️ **Configurable**: Comprehensive configuration system for different environments
- 🏗️ **Builder Pattern**: Fluent interface for easy payment creation
- 📝 **Type Safe**: Full type hints and IDE support
- 🧪 **Well Tested**: Comprehensive test suite with examples

## Installation

### Option 1: Using pip (when published)
```bash
pip install buckaroo-sdk-python
```

### Option 2: From source
```bash
# Clone the repository
git clone https://github.com/buckaroo-it/BuckarooSDK_Python.git
cd BuckarooSDK_Python

# Install dependencies
pip install -r requirements.txt

# Or use the installation script
chmod +x install.sh
./install.sh
```

### Requirements

- Python 3.6 or higher
- requests >= 2.20.0
- urllib3 >= 1.25.0
- typing_extensions >= 4.5.0 (for Python 3.7+)

## Quick Start

```python
from buckaroo._buckaroo_client import BuckarooClient

# Initialize the client
client = BuckarooClient("your_store_key", "your_secret_key", mode="test")

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

# Execute the payment
result = payment.execute()
print(f"Payment Key: {result['payment_key']}")
print(f"Redirect URL: {result['redirect_url']}")
```

## Configuration

### Basic Configuration
```python
# Using mode string (backward compatible)
client = BuckarooClient("store_key", "secret_key", mode="test")  # or "live"
```

### Advanced Configuration
```python
from buckaroo.config.buckaroo_config import BuckarooConfig, Environment, ConfigBuilder

# Using BuckarooConfig
config = BuckarooConfig(
    environment=Environment.LIVE,
    timeout=60,
    retry_attempts=5,
    logging_enabled=True
)
client = BuckarooClient("store_key", "secret_key", config=config)

# Using ConfigBuilder (fluent interface)
config = (ConfigBuilder()
         .live_environment()
         .timeout(45)
         .retry_attempts(3)
         .enable_logging()
         .build())
client = BuckarooClient("store_key", "secret_key", config=config)
```

## Payment Methods

### iDEAL
```python
payment = (client.payments.create_payment("ideal")
          .currency("EUR")
          .amount_debit(25.00)
          .issuer("ABNANL2A")
          .description("iDEAL payment")
          .invoice("IDEAL-001"))
```

### Apple Pay
```python
payment = (client.payments.create_payment("applepay")
          .payment_data("encrypted_apple_pay_token")
          .customer_card_name("John Doe")
          .currency("EUR")
          .amount_debit(49.99))
```

### iDEAL QR
```python
payment = (client.payments.create_payment("idealqr")
          .description("QR Code payment")
          .purchase_id("QR-001")
          .amount(15.00)
          .image_size(2000)
          .expiration("2024-12-31"))
```

### Credit Card
```python
payment = (client.payments.create_payment("creditcard")
          .card_number("4111111111111111")
          .expiry_month(12)
          .expiry_year(2025)
          .cvv("123")
          .cardholder_name("John Doe"))
```

### PayPal
```python
payment = (client.payments.create_payment("paypal")
          .currency("EUR")
          .amount_debit(30.00)
          .description("PayPal payment"))
```

## Dictionary Parameters

You can also use dictionary parameters for quick setup:

```python
# iDEAL with dictionary
ideal_params = {
    'currency': 'EUR',
    'amount_debit': 25.00,
    'description': 'Dictionary payment',
    'invoice': 'DICT-001',
    'issuer': 'ABNANL2A'
}
payment = client.payments.create_payment("ideal", ideal_params)

# Apple Pay with service parameters
apple_params = {
    'currency': 'EUR',
    'amount_debit': 49.99,
    'service_parameters': {
        'PaymentData': 'encrypted_token',
        'CustomerCardName': 'Jane Doe'
    }
}
payment = client.payments.create_payment("applepay", apple_params)
```

## Error Handling

```python
from buckaroo.exceptions._authentication_error import AuthenticationError
from buckaroo.http.client import BuckarooApiError

try:
    result = payment.execute()
    
    if result['is_successful_payment']:
        print("Payment successful!")
        print(f"Payment Key: {result['payment_key']}")
    else:
        print(f"Payment failed: {result['buckaroo_status_message']}")
        
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except BuckarooApiError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing Installation

Run the installation test to verify everything is working:

```bash
python test_installation.py
```

## Examples

Check the `examples/` directory for comprehensive usage examples:

- `ideal_payment_example.py` - iDEAL payment examples
- `applepay_payment_example.py` - Apple Pay examples
- `idealqr_payment_example.py` - iDEAL QR examples
- `buckaroo_config_example.py` - Configuration examples
- `http_request_example.py` - HTTP functionality examples

## Development

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Run Tests
```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_buckaroo_client

# Run with coverage
pytest --cov=buckaroo tests/
```

### Code Formatting
```bash
# Format code
black buckaroo/ tests/ examples/

# Sort imports
isort buckaroo/ tests/ examples/

# Lint code
flake8 buckaroo/ tests/ examples/
```

## API Documentation

For detailed API documentation, visit: [Buckaroo API Documentation](https://dev.buckaroo.nl/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.

## Support

- 📧 Email: wecare@buckaroo.nl
- 🐛 Issues: [GitHub Issues](https://github.com/buckaroo-it/BuckarooSDK_Python/issues)
- 📖 Documentation: [Buckaroo Developer Portal](https://dev.buckaroo.nl/)

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.