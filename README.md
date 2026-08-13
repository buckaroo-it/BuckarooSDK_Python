<p align="center">
  <a href="https://www.buckaroo.nl">
    <img src="https://raw.githubusercontent.com/buckaroo-it/Media/main/Buckaroo/README.md%20Headers/buckaroo-python-sdk-header-rounded.png" alt="Buckaroo — Python SDK" width="100%">
  </a>
</p>

<h1 align="center">Buckaroo Python SDK</h1>

<p align="center">
  <a href="https://pypi.org/project/buckaroo-sdk/"><img src="https://img.shields.io/pypi/v/buckaroo-sdk.svg?label=release" alt="Latest release"></a>
  <a href="https://pypi.org/project/buckaroo-sdk/"><img src="https://img.shields.io/pypi/pyversions/buckaroo-sdk.svg?label=Python" alt="Python versions"></a>
  <a href="https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/LICENSE.txt"><img src="https://img.shields.io/pypi/l/buckaroo-sdk.svg?label=license" alt="License"></a>
  <a href="https://docs.buckaroo.io/docs/python-sdk"><img src="https://img.shields.io/badge/docs-docs.buckaroo.io-1a1a4b.svg" alt="Documentation"></a>
</p>

<p align="center">
  <a href="#about">About</a> &middot;
  <a href="#requirements">Requirements</a> &middot;
  <a href="#installation">Installation</a> &middot;
  <a href="#getting-started">Getting started</a> &middot;
  <a href="#buckaroo-solutions">Buckaroo solutions</a> &middot;
  <a href="#testing">Testing</a> &middot;
  <a href="#support">Support</a> &middot;
  <a href="#contribute">Contribute</a>
</p>

---

## About

Buckaroo is a Dutch Payment Service Provider. More than 54,000 organisations rely on the Buckaroo platform to process their payments, subscriptions and unpaid invoices.

This is Buckaroo's official Python SDK: a modern, open source library that connects a Python application to the Buckaroo API. Beyond payments and refunds it covers iDIN identity verification, eMandates, Split Payments, Credit Management and Point of Sale.

If you run a shop on an e-commerce platform, use the ready-made plugin for [Magento 2](https://github.com/buckaroo-it/Magento2), [Shopware 6](https://github.com/buckaroo-it/Shopware6), [WooCommerce](https://github.com/buckaroo-it/WooCommerce), [PrestaShop](https://github.com/buckaroo-it/PrestaShop) or [Odoo](https://github.com/buckaroo-it/Odoo) instead. This SDK is for custom applications.

[Full API documentation on docs.buckaroo.io](https://docs.buckaroo.io/reference)

---

## Requirements

| Requirement | Supported versions |
|---|---|
| Python | 3.9 or higher |
| OpenSSL | An up-to-date SSL/TLS toolkit |

You also need a Buckaroo account. Don't have one yet? [Request an account](https://www.buckaroo.nl/start).

---

## Installation

Install the SDK with [pip](https://pip.pypa.io/):

```bash
pip install buckaroo-sdk
```

---

## Getting started

### Configuring the client

You can find your Store key and Secret key under [API credentials in Buckaroo Plaza](https://plaza.buckaroo.nl/Configuration/Merchant/ApiKeys). Set `mode` to `test` while developing and to `live` in production.

```python
from buckaroo import BuckarooClient
from buckaroo.services.payment_service import PaymentService

client = BuckarooClient("STORE_KEY", "SECRET_KEY", mode="test")
payments = PaymentService(client)
```

Alternatively, read the credentials from the environment. Copy `.env.example` to `.env`, fill it in, and use:

```python
from buckaroo.app import Buckaroo

app = Buckaroo.from_env()
```

This gives you `app.payments` and `app.solutions`, which are used interchangeably with `PaymentService` and `SolutionService` throughout the examples below.

### Creating a payment

Every payment method takes a slightly different payload. This example charges a Visa card:

```python
response = (
    payments.create_payment(
        "creditcard",
        {
            "currency": "EUR",
            "amount": 10.00,
            "invoice": "UNIQUE-INVOICE-NO",  # must be unique per payment
            "service_parameters": {"brand": "visa"},
        },
    )
    .description("Order #UNIQUE-INVOICE-NO")
    .pay()
)

if response.is_successful():
    print("transaction id:", response.get_transaction_id())
    print("redirect:", response.get_redirect_url())
else:
    print("status message:", response.get_message())
```

The same request can be built with the fluent interface:

```python
response = (
    payments.create_payment("creditcard")
    .currency("EUR")
    .amount(10.00)
    .invoice("UNIQUE-INVOICE-NO")
    .pay()
)
```

Service codes for every payment method are listed in the [API reference](https://docs.buckaroo.io/reference).

---

## Buckaroo solutions

### iDIN

iDIN lets Dutch banks confirm a consumer's identity on your behalf. It carries no amount or currency, only the return URLs plus the `issuerId` service parameter, which is the BIC code of the consumer's bank. Three actions are available: `identify()`, `verify()` for age 18+, and `login()`.

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

Runnable demo of all three actions: [`examples/idin.py`](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/examples/idin.py).

### Instant refunds

Instant refunds return money to the shopper immediately rather than through the regular batch refund process, and are processed as an instant payment instead of a standard refund. They are supported for iDEAL. Pass the `original_transaction_key` of a settled payment. `refund_amount` is optional, so omit it for a full refund.

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

Runnable demo: [`examples/instant_refund.py`](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/examples/instant_refund.py).

### eMandate

eMandate is a DataRequest-based solution for managing SEPA direct debit mandates, reached through `app.solutions` rather than `app.payments`. Two variants share the same five actions, differing only in service name: `emandate` for retail (B2C) and `emandateb2b` for business (B2B).

```python
from buckaroo.app import Buckaroo

app = Buckaroo.from_env()

# GetIssuerList - no parameters
response = app.solutions.create_solution("emandate").issuer_list()

# CreateMandate - debtorReference is required
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

# GetStatus - mandateId is required
response = app.solutions.create_solution(
    "emandate", {"service_parameters": {"mandateId": mandate_id}}
).status()

# ModifyMandate - mandateId is required
response = app.solutions.create_solution(
    "emandate",
    {"service_parameters": {"mandateId": mandate_id, "maxAmount": "1000.00"}},
).modify_mandate()

# CancelMandate - mandateId is required
response = app.solutions.create_solution(
    "emandate",
    {"service_parameters": {"mandateId": mandate_id, "purchaseId": "PUR-001"}},
).cancel_mandate()
```

Swap `"emandate"` for `"emandateb2b"` to use the B2B variant. Runnable demo of all five actions against both services: [`examples/emandate.py`](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/examples/emandate.py).

### Split payments

Split Payments (Buckaroo service `Marketplaces`) lets a platform divide one customer payment across its own funds account and one or more seller accounts. `split` and `refund_supplementary` build a supplementary service that is *combined* into a payment or refund; `transfer` and `manual_transfer` are standalone.

```python
from buckaroo import BuckarooClient
from buckaroo.services.payment_service import PaymentService
from buckaroo.services.solution_service import SolutionService

client = BuckarooClient("STORE_KEY", "SECRET_KEY", mode="test")
payments = PaymentService(client)
marketplaces = SolutionService(client)
```

**Split** — build the split, then combine it into the funding payment. Set `daysUntilTransfer` to `"0"` for immediate payout, or omit it to hold the funds until a later Transfer.

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

**Transfer** — release the held funds of an existing split payment. With no split data it transfers everything (Transfer I); pass `marketplace` or `sellers` for a partial or re-specified split (Transfer II).

```python
marketplaces.create_solution("marketplaces").transfer(
    {"originalTransactionKey": "SPLIT_TRANSACTION_KEY"}
)
```

**RefundSupplementary** — refund the consumer and pull the funds back from the target accounts, combined into the refund. Without seller data it reverts all transfers; pass `sellers` to retrieve specific amounts per account.

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

Runnable demo of all six request types: [`examples/marketplaces.py`](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/examples/marketplaces.py).

### Credit management

Credit Management is a DataRequest-based solution for invoicing and debtor administration, reached through `app.solutions`. It covers creating and pausing invoices, managing debtors and their files, credit notes, product lines and payment plans. `create_combined_invoice` is the exception: it builds a supplementary service that is *combined* into a funding payment or refund, like Split Payments.

> [!IMPORTANT]
> `invoice` and `currency` are **top-level** request fields for `CreateInvoice`, `CreateCombinedInvoice`, `CreateCreditNote`, `PauseInvoice`, `UnPauseInvoice` and `InvoiceInfo`. Set them through the top-level payload keys or `.invoice(...)` and `.currency(...)`, not inside `service_parameters` — the gateway rejects them there with `ParameterMissing`. The same applies to `description` for `CreatePaymentPlan`, which the gateway rejects as an unknown parameter when sent as a service parameter.

> [!NOTE]
> `schemeKey` is store-specific and must belong to the same store as your Store key. The `txnpk6` value below is the scheme of the demo account these examples were written against — replace it with the scheme key configured for your own store, found in Plaza under **Credit Management → CM scheme settings**.

```python
from buckaroo.app import Buckaroo

app = Buckaroo.from_env()

# CreateInvoice - invoiceAmount, dueDate, schemeKey and a Debtor group with a
# code are required; invoice and currency go top-level
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

# AddOrUpdateDebtor - a Debtor group with a code is required;
# Person, Company, Address, Email and Phone groups are optional
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

# DebtorInfo - a Debtor group with a code is required
response = app.solutions.create_solution(
    "creditmanagement",
    {"service_parameters": {"debtor": {"code": "DEBTOR-001"}}},
).debtor_info()

# AddOrUpdateProductLines - articles are passed as the `articles` method
# argument, not through service_parameters; each article requires type,
# totalAmount and totalVat alongside the usual fields
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

# CreatePaymentPlan - includedInvoiceKey, dossierNumber, startDate, interval,
# paymentPlanCostAmount and recipientEmail are required service parameters;
# description goes top-level; either installmentCount or installmentAmount is
# also required. Needs an active Credit Management subscription and an included
# invoice past its due date, both enforced by the gateway rather than the SDK
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

# InvoiceInfo - invoice is required, top-level
response = app.solutions.create_solution(
    "creditmanagement", {"invoice": "INV-001"}
).invoice_info()
```

`create_combined_invoice` accepts the same invoice service fields as `create_invoice`, including the `Debtor` group. A combined request has a single shared top level, so `invoice` and `currency` are set on the *funding* payment rather than on the CreditManagement3 sub-builder:

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

The remaining actions follow the same shape: `create_credit_note` with `invoice` top-level and `originalInvoiceNumber` plus `Debtor` as service parameters, `resume_debtor_file` and `pause_debtor_file`, `pause_invoice` and `unpause_invoice` with `invoice` top-level and no service parameters, and `terminate_payment_plan` with `includedInvoiceKey`.

Runnable demo of the main actions: [`examples/credit_management.py`](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/examples/credit_management.py).

### Point of Sale

> [!WARNING]
> This is the older POS solution. It has been replaced by UPG, which is not part of this SDK — see the [UPG documentation](https://docs.buckaroo.io/v2/docs/authentication) if you are building a new in-store integration.

POS transactions are PIN-based in-store payments processed through a physical payment terminal. You initiate the transaction via the API with the terminal's `TerminalID`, and Buckaroo routes the request to that terminal, which prompts the customer to complete payment there. There is no redirect flow, and every request is sent with a fixed `Channel: "Web"` that the SDK sets internally.

The immediate response carries a pending status. The final result, along with the printable `Ticket` receipt text, arrives later by push notification.

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

Push bodies wrap the transaction under a `Transaction` key, so unwrap it before handing it to `PaymentResponse`:

```python
from buckaroo.models.payment_response import PaymentResponse

transaction = push_json["Transaction"]  # raw body your webhook endpoint received
response = PaymentResponse({"data": transaction})

ticket = response.get_service_parameter("Ticket")  # printable receipt text
```

Runnable demo of both the Pay action and push parsing: [`examples/pos_payment.py`](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/examples/pos_payment.py).

---

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The runnable examples in [`examples/`](https://github.com/buckaroo-it/BuckarooSDK_Python/tree/master/examples) expect credentials in a `.env` file. Copy `.env.example` and fill in your test Store key and Secret key.

---

## Support

Having trouble? Work through this list before reaching out:

1. Check the [API reference](https://docs.buckaroo.io/reference) for the service and action you are calling.
2. Confirm you are on the [latest release](https://github.com/buckaroo-it/BuckarooSDK_Python/releases).
3. Reproduce the issue with `mode="test"` and inspect `response.get_message()` and the raw response.
4. Verify that your push URL is reachable from outside your network. Buckaroo sends push messages from fixed IP addresses and ports, so make sure these are on your allow list. See [push messages](https://docs.buckaroo.io/docs/integration-push-messages) for the current list.

Still stuck? Contact us and include your Python version, SDK version, the service and action you called, the error message and the transaction key.

- **Bug reports and feature requests:** [open an issue](https://github.com/buckaroo-it/BuckarooSDK_Python/issues)
- **Technical support:** [support@buckaroo.nl](mailto:support@buckaroo.nl)
- **Phone:** +31 (0)30 711 50 50
- **Gateway status:** [status.buckaroo.io](https://status.buckaroo.io/)

---

## Contribute

We really appreciate it when developers help improve the Buckaroo SDKs. Please read our [Contribution Guidelines](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/CONTRIBUTING.md) before opening a pull request, and target the `master` branch.

Found a security issue? Please report it privately to [support@buckaroo.nl](mailto:support@buckaroo.nl) instead of opening a public issue.

---

## Versioning

We follow semantic versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR** — breaking changes that require additional testing and caution.
- **MINOR** — new functionality with limited impact.
- **PATCH** — bug fixes and hotfixes only.

All changes are documented in the [changelog](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/CHANGELOG.md) and on the [releases page](https://github.com/buckaroo-it/BuckarooSDK_Python/releases).

---

## License

This SDK is open source software licensed under the [MIT license](https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/LICENSE.txt).

---

<p align="center">
  <sub>Made with care by <a href="https://www.buckaroo.nl">Buckaroo</a>.<br>
  This document is subject to change; typos and language errors are possible.</sub>
</p>
