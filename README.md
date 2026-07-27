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
- [Split Payments](#split-payments)
- [Credit Management](#credit-management)
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
    payments.create_payment(
        "creditcard",
        {
            "currency": "EUR",
            "amount": 10.00,  # The amount we want to charge
            "invoice": "UNIQUE-INVOICE-NO",  # Each payment must contain a unique invoice number
            "service_parameters": {"brand": "visa"},  # Request to pay with Visa
        },
    )
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
response = payments.create_payment(
    "idin",
    {
        "return_url": "https://www.buckaroo.nl",
        "return_url_cancel": "https://www.buckaroo.nl/cancel",
        "return_url_error": "https://www.buckaroo.nl/error",
        "return_url_reject": "https://www.buckaroo.nl/reject",
        "service_parameters": {"issuerId": "BANKNL2Y"},  # sandbox issuer
    },
).identify()

print("key:", response.key)
print("redirect:", response.get_redirect_url())
```

See [`examples/idin.py`](examples/idin.py) for a runnable demo of all three actions.

### Instant Refunds

Instant refunds send money back to the shopper immediately instead of via the regular batch refund process. They are processed as an instant payment rather than a standard refund, and are supported for iDEAL and Payconiq via `instantRefund()`. Pass the `original_transaction_key` of a settled payment; `refund_amount` is optional — omit it for a full refund.

```python
response = payments.create_payment(
    "ideal",
    {
        "currency": "EUR",
        "description": "ideal instant refund demo",
        "invoice": "IDEAL-REFUND-DEMO-001",
        "original_transaction_key": "ORIGINAL-TRANSACTION-KEY",
        "refund_amount": 12.34,  # optional; omit for a full refund
    },
).instantRefund()

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

### Split Payments

Split Payments (Buckaroo service `Marketplaces`) lets a platform divide one
customer payment across its own funds account and one or more seller accounts.
Following the other Buckaroo SDKs, `split` and `refund_supplementary` build a
supplementary service that is *combined* into a payment or refund; `transfer` and
`manual_transfer` are standalone.

```python
from buckaroo import BuckarooClient
from buckaroo.services.payment_service import PaymentService
from buckaroo.services.solution_service import SolutionService

client = BuckarooClient("STORE_KEY", "SECRET_KEY", mode="test")
payments = PaymentService(client)
marketplaces = SolutionService(client)
```

**Split** — build the split, then combine it into the funding payment (e.g.
iDEAL). `daysUntilTransfer` is `"0"` for immediate payout, or omit it to hold the
funds until a later Transfer.

```python
split = marketplaces.create_solution("marketplaces").split(
    {
        "daysUntilTransfer": "2",
        "marketplace": {"Amount": "10.00", "Description": "INV0001 Commission Platform"},
        "sellers": [
            {"AccountId": "SELLER_ACCOUNT_1", "Amount": "50.00", "Description": "Payout 1"},
            {"AccountId": "SELLER_ACCOUNT_2", "Amount": "35.00", "Description": "Payout 2"},
        ],
    }
)

response = (
    payments.create_payment(
        "ideal",
        {
            "currency": "EUR",
            "amount": 95.00,
            "invoice": "INV0001",
            "description": "Split order INV0001",
            "service_parameters": {"issuer": "ABNANL2A"},
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        },
    )
    .combine(split)
    .pay()
)
```

**Transfer** — release held funds of an existing split payment. With no split
data it transfers everything (Transfer I); pass `marketplace`/`sellers` to
transfer a partial or re-specified split (Transfer II).

```python
marketplaces.create_solution("marketplaces").transfer(
    {
        "originalTransactionKey": "SPLIT_TRANSACTION_KEY",
    }
)
```

**RefundSupplementary** — refund the consumer and pull the funds back from the
target accounts. Combine it into the refund. Without seller data it reverts all
transfers (I); pass `sellers` to retrieve specific amounts per account (II).

```python
supplementary = marketplaces.create_solution("marketplaces").refund_supplementary()

payments.create_payment(
    "ideal",
    {
        "currency": "EUR",
        "amount": 50.00,
        "invoice": "INV0001",
        "description": "Split refund INV0001",
        "original_transaction_key": "SPLIT_TRANSACTION_KEY",
        "refund_amount": 50.00,
        "return_url": "https://example.com/return",
        "return_url_cancel": "https://example.com/cancel",
        "return_url_error": "https://example.com/error",
        "return_url_reject": "https://example.com/reject",
    },
).combine(supplementary).refund()
```

**ManualTransfer** — move funds directly between two accounts.

```python
marketplaces.create_solution("marketplaces").manual_transfer(
    {
        "fromAccountId": "ACCOUNT_A",
        "toAccountId": "ACCOUNT_B",
        "fromDescription": "Deduction monthly fee",
        "toDescription": "Monthly fee third party ABC",
        "amount": 10.00,
        "currency": "EUR",
    }
)
```

A runnable demo of all six request types is in
[`examples/marketplaces.py`](examples/marketplaces.py).

### Credit Management

Credit Management is a DataRequest-based solution for invoicing and debtor
administration, reached through `app.solutions` rather than `app.payments`.
It covers creating and pausing invoices, managing debtors and their files,
credit notes, product lines, and payment plans. `create_combined_invoice` is
the exception — it builds a supplementary service that is *combined* into a
funding payment or refund, like Split Payments.

`invoice` and `currency` are **top-level** request fields for `CreateInvoice`,
`CreateCombinedInvoice`, `CreateCreditNote`, `PauseInvoice`, `UnPauseInvoice`
and `InvoiceInfo` — set them via the top-level `invoice`/`currency` payload
keys (or `.invoice(...)`/`.currency(...)`), not inside `service_parameters`.
The gateway rejects them as service parameters with `ParameterMissing`.
`description` is likewise a **top-level** request field for
`CreatePaymentPlan` — set it via the top-level `description` payload key (or
`.description(...)`), not inside `service_parameters`. The gateway rejects it
as an unknown parameter when sent as one.
`schemeKey` is store-specific: it must belong to the same store as your store
key. `txnpk6` below is the scheme of the demo account used to write these
examples — replace it with the scheme key configured for your own store
(Plaza → Credit Management → CM scheme settings).

```python
from buckaroo.app import Buckaroo

app = Buckaroo.from_env()

# Create an invoice (CreateInvoice — invoiceAmount, dueDate, schemeKey and a
# Debtor group with a code are required; invoice/currency go top-level)
response = app.solutions.create_solution(
    "creditmanagement",
    {
        "invoice": "INV-001",
        "currency": "EUR",
        "service_parameters": {
            "invoiceAmount": "250.00",
            "dueDate": "2026-09-01",
            "schemeKey": "txnpk6",
            "debtor": {"code": "DEBTOR-001"},
        },
    },
).create_invoice()
invoice_key = response.get_service_parameter("InvoiceKey")

# Create or update a debtor (AddOrUpdateDebtor — a Debtor group with a code
# is required; Person/Company/Address/Email/Phone groups are optional)
response = app.solutions.create_solution(
    "creditmanagement",
    {
        "service_parameters": {
            "debtor": {"code": "DEBTOR-001"},
            "person": {"firstName": "John", "lastName": "Doe"},
            "address": {"street": "Main St", "city": "Amsterdam"},
        }
    },
).add_or_update_debtor()

# Look up a debtor (DebtorInfo — a Debtor group with a code is required)
response = app.solutions.create_solution(
    "creditmanagement",
    {"service_parameters": {"debtor": {"code": "DEBTOR-001"}}},
).debtor_info()

# Add product lines (AddOrUpdateProductLines — articles must be passed as
# the `articles` method argument, not through service_parameters; each
# article requires type, totalAmount and totalVat on top of the usual
# identifier/description/quantity/price)
builder = app.solutions.create_solution(
    "creditmanagement",
    {"service_parameters": {"invoiceKey": "INVK-001"}},
)
response = builder.add_or_update_product_lines(
    articles=[
        {
            "identifier": "SKU-1",
            "description": "Widget",
            "quantity": "2",
            "price": "10.00",
            "type": "Regular",
            "totalAmount": "20.00",
            "totalVat": "4.20",
            "vatPercentage": "21",
        },
    ]
)

# Create a payment plan (CreatePaymentPlan — includedInvoiceKey,
# dossierNumber, startDate, interval, paymentPlanCostAmount and
# recipientEmail are required service parameters; description goes
# top-level; either installmentCount or installmentAmount must also be
# given. Requires an active Buckaroo Credit Management subscription and an
# included invoice past its due date — enforced by the gateway, not the SDK)
response = app.solutions.create_solution(
    "creditmanagement",
    {
        "description": "3-month plan",
        "service_parameters": {
            "includedInvoiceKey": "INVK-001",
            "dossierNumber": "DOSSIER-001",
            "startDate": "2026-09-01",
            "interval": "Month",
            "paymentPlanCostAmount": "5.00",
            "recipientEmail": "debtor@example.com",
            "installmentCount": "3",
        },
    },
).create_payment_plan()

# Look up an invoice (InvoiceInfo — invoice is required, top-level)
response = app.solutions.create_solution("creditmanagement", {"invoice": "INV-001"}).invoice_info()
```

`create_combined_invoice` accepts the same invoice service fields as
`create_invoice`, including the `Debtor` group, and combines into the
funding payment or refund. The combined request has a single shared top
level, so `invoice`/`currency` are set on the *funding* payment, not on the
CreditManagement3 sub-builder:

```python
cm = app.solutions.create_solution(
    "creditmanagement",
    {
        "service_parameters": {
            "invoiceAmount": "95.00",
            "dueDate": "2026-09-01",
            "schemeKey": "txnpk6",
            "debtor": {"code": "DEBTOR-001"},
        }
    },
).create_combined_invoice()

response = (
    app.payments.create_payment(
        "ideal",
        {
            "currency": "EUR",
            "amount": 95.00,
            "invoice": "INV-002",
            "description": "Combined invoice order INV-002",
            "service_parameters": {"issuer": "ABNANL2A"},
            "return_url": "https://example.com/return",
            "return_url_cancel": "https://example.com/cancel",
            "return_url_error": "https://example.com/error",
            "return_url_reject": "https://example.com/reject",
        },
    )
    .combine(cm)
    .pay()
)
```

Other actions follow the same shape: `create_credit_note` (`invoice`
top-level, `originalInvoiceNumber` and `Debtor` as service parameters),
`resume_debtor_file`/`pause_debtor_file`, `pause_invoice`/`unpause_invoice`
(`invoice` top-level, no service parameters), and `terminate_payment_plan`
(`includedInvoiceKey`).

See [`examples/credit_management.py`](examples/credit_management.py) for a
runnable demo of the main actions.

### Point of Sale (POS)

POS transactions are PIN-based in-store payments processed through a physical payment terminal.
You initiate the transaction via API with the terminal's unique `TerminalID`; Buckaroo routes the
request to that terminal, which prompts the customer to complete payment there. There's no
redirect flow, every request is sent with a fixed `Channel: "Web"`, set internally by the SDK.

The immediate response carries a pending/awaiting status. The final result, plus the printable
`Ticket` receipt text for the customer, arrives later via push notification.

```python
response = (
    payments.create_payment(
        "pospayment",
        {
            "currency": "EUR",
            "amount": 0.01,
            "invoice": "TestFactuur01",
        },
    )
    .terminal_id("50000001")
    .pay()
)

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
