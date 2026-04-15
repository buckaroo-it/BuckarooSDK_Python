# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-15

### Added
- Initial release of the Buckaroo Python SDK
- Payment method builders for iDEAL, Credit Card, Apple Pay, Google Pay, Bancontact, Alipay, Sofort, Payconiq, iDEAL QR, KBC, MBWay, Multibanco, PayPal, Przelewy24, Riverty, SEPA Direct Debit, Swish, Transfer, Trustly, Twint, Voucher, WeChatPay, Wero, Giftcards, Belfius, Bizum, Blik, BuckarooVoucher, ClickToPay, EPS, ExternalPayment, In3, Klarna, KlarnaKP, Knaken, PayByBank
- Solution builders: SolutionBuilder, SubscriptionBuilder
- Strategy-based HTTP client (requests library or system curl)
- HMAC-SHA256 authentication following Buckaroo API specification
- Configurable logging observer with sensitive data masking
- Parameter validation with strict and non-strict modes
- Authorize/capture capability for credit card payments
- Encrypted payment support for credit cards
- Fast checkout support for iDEAL
- Instant refund support for applicable payment methods
- Factory pattern for payment method and solution builders
- Docker Compose setup for local development
