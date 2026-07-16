<p align="center">
  <img src="https://www.buckaroo.nl/media/bldbj0zn/python-sdk_icon.png" width="200px" position="center">
</p>

# Buckaroo Python SDK
[![Latest release](https://badgen.net/github/release/buckaroo-it/BuckarooSDK_Python)](https://github.com/buckaroo-it/BuckarooSDK_Python/releases)

---
### Index
- [About](#about)
- [Requirements](#requirements)
- [Pip Installation](#pip-installation)
- [Example](#example)
- [iDIN](#idin)
- [Instant Refunds](#instant-refunds)
- [eMandate](#emandate)
- [Point of Sale (POS)](#point-of-sale-pos)
- [Contribute](#contribute)
- [Versioning](#versioning)
- [Additional information](#additional-information)
---

### About

Buckaroo is the Payment Service Provider for all your online payments with more than 30,000 companies relying on Buckaroo's platform to securely process their payments, subscriptions and unpaid invoices.
Buckaroo developed their own Python SDK. The SDK is a modern, open-source Python library that makes it easy to integrate your Python application with Buckaroo's services.
Start accepting payments today with Buckaroo.

### Requirements

To use the Buckaroo API client, the following things are required:

+ A Buckaroo account ([Dutch](https://www.buckaroo.nl/start) or [English](https://www.buckaroo.eu/solutions/request-form))
+ Python >= 3.9
+ Up-to-date OpenSSL (or other SSL/TLS toolkit)

### Pip Installation

By far the easiest way to install the Buckaroo SDK is via [pip](https://pip.pypa.io/).

    $ pip install buckaroo-sdk

Then import the client in your project:

```python
from buckaroo import BuckarooClient
```

### Example
Create and configure the Buckaroo client.
You can find your credentials in [Buckaroo Plaza](https://plaza.buckaroo.nl/Configuration/Merchant/ApiKeys).

```python
from buckaroo import BuckarooClient
from buckaroo.services.payment_service import PaymentService

# Get your store & secret key in your plaza.
# mode="test" routes calls to the test environment; use "live" for production.
client = BuckarooClient("STORE_KEY", "SECRET_KEY", mode="test")
payments = PaymentService(client)
```

Create a payment with any of the available payment methods. In this example, we show how to create a credit card payment. Each payment has a slightly different payload.

```python
# Create a new payment
response = (
    payments.create_payment("creditcard", {
        "currency": "EUR",
        "amount": 10.00,                       # The amount we want to charge
        "invoice": "UNIQUE-INVOICE-NO",        # Each payment must contain a unique invoice number
        "service_parameters": {"brand": "visa"},  # Request to pay with Visa
    })
    .description("Order #UNIQUE-INVOICE-NO")
    .pay()
)

# Inspect the response from Buckaroo
if response.is_successful():
    print("transaction id:", response.get_transaction_id())
    print("redirect:", response.get_redirect_url())
else:
    print("status message:", response.get_message())
```

You can also use the fluent interface directly:

```python
response = (
    payments.create_payment("creditcard")
        .currency("EUR")
        .amount(10.00)
        .invoice("UNIQUE-INVOICE-NO")
        .pay()
)
```

Find our full documentation online on [docs.buckaroo.io](https://docs.buckaroo.io).

### iDIN

iDIN lets Dutch banks confirm a consumer's identity on your behalf. It carries no amount or currency — only the return URLs plus the `issuerId` (BIC code of the consumer's bank) service parameter. Three actions are available: `identify()`, `verify()` (age 18+), and `login()`.

```python
response = payments.create_payment("idin", {
    "return_url": "https://www.buckaroo.nl",
    "return_url_cancel": "https://www.buckaroo.nl/cancel",
    "return_url_error": "https://www.buckaroo.nl/error",
    "return_url_reject": "https://www.buckaroo.nl/reject",
    "service_parameters": {"issuerId": "BANKNL2Y"},  # sandbox issuer
}).identify()

print("key:", response.key)
print("redirect:", response.get_redirect_url())
```

See [`examples/idin.py`](examples/idin.py) for a runnable demo of all three actions.

### Instant Refunds

Instant refunds send money back to the shopper immediately instead of via the regular batch refund process. They are processed as an instant payment rather than a standard refund, and are supported for iDEAL and Payconiq via `instantRefund()`. Pass the `original_transaction_key` of a settled payment; `refund_amount` is optional — omit it for a full refund.

```python
response = payments.create_payment("ideal", {
    "currency": "EUR",
    "description": "ideal instant refund demo",
    "invoice": "IDEAL-REFUND-DEMO-001",
    "original_transaction_key": "ORIGINAL-TRANSACTION-KEY",
    "refund_amount": 12.34,  # optional; omit for a full refund
}).instantRefund()

print("key:", response.key)
```

See [`examples/instant_refund.py`](examples/instant_refund.py) for a runnable demo covering both iDEAL and Payconiq.

### eMandate

eMandate is a DataRequest-based solution for managing SEPA direct debit mandates, reached through
`app.solutions` rather than `app.payments`. It comes in two variants that share the same five
actions — only the service name differs:

- `emandate` — retail (B2C)
- `emandateb2b` — business (B2B)

```python
from buckaroo.app import Buckaroo

app = Buckaroo.from_env()

# List available issuers (GetIssuerList — no parameters)
response = app.solutions.create_solution("emandate").issuer_list()

# Create a mandate (CreateMandate — debtorReference is required)
response = app.solutions.create_solution(
    "emandate",
    {
        "service_parameters": {
            "debtorReference": "DEBTOR-001",
            "debtorBankId": "ABNANL2A",
            "sequenceType": "1",
            "purchaseId": "PUR-001",
            "language": "nl",
        }
    },
).create_mandate()
mandate_id = response.get_service_parameter("MandateId")

# Look up a mandate's status (GetStatus — mandateId is required)
response = app.solutions.create_solution(
    "emandate", {"service_parameters": {"mandateId": mandate_id}}
).status()

# Modify a mandate (ModifyMandate — mandateId is required)
response = app.solutions.create_solution(
    "emandate",
    {"service_parameters": {"mandateId": mandate_id, "maxAmount": "1000.00"}},
).modify_mandate()

# Cancel a mandate (CancelMandate — mandateId is required)
response = app.solutions.create_solution(
    "emandate",
    {"service_parameters": {"mandateId": mandate_id, "purchaseId": "PUR-001"}},
).cancel_mandate()
```

The B2B variant exposes the same five methods — swap `"emandate"` for `"emandateb2b"`.

See [`examples/emandate.py`](examples/emandate.py) for a runnable demo of all five actions
against both the B2C and B2B services.

### Point of Sale (POS)

POS transactions are PIN-based in-store payments processed through a physical payment terminal.
You initiate the transaction via API with the terminal's unique `TerminalID`; Buckaroo routes the
request to that terminal, which prompts the customer to complete payment there. There's no
redirect flow, every request is sent with a fixed `Channel: "Web"`, set internally by the SDK.

The immediate response carries a pending/awaiting status. The final result, plus the printable
`Ticket` receipt text for the customer, arrives later via push notification.

```python
response = payments.create_payment("pospayment", {
    "currency": "EUR",
    "amount": 0.01,
    "invoice": "TestFactuur01",
}).terminal_id("50000001").pay()

print("key:", response.key)
print("pending:", response.is_pending())
```

Parsing the push notification once the terminal completes the transaction push bodies wrap the
transaction under a `Transaction` key, so unwrap it before handing it to `PaymentResponse`:

```python
from buckaroo.models.payment_response import PaymentResponse

transaction = push_json["Transaction"]  # raw body your webhook endpoint received
response = PaymentResponse({"data": transaction})

ticket = response.get_service_parameter("Ticket")  # printable receipt text
```

See [`examples/pos_payment.py`](examples/pos_payment.py) for a runnable demo of both the `Pay`
action and push-notification parsing.

### Contribute

We really appreciate it when developers contribute to improve the Buckaroo plugins.
If you want to contribute as well, then please follow our [Contribution Guidelines](CONTRIBUTING.md).

### Versioning

- **MAJOR:** Breaking changes that require additional testing/caution
- **MINOR:** Changes that should not have a big impact
- **PATCHES:** Bug and hotfixes only

### Additional information
- **Support:** https://docs.buckaroo.io/docs/contact-us
- **Contact:** [support@buckaroo.nl](mailto:support@buckaroo.nl) or [+31 (0)30 711 50 50](tel:+310307115050)

## License
Buckaroo Python SDK is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).
