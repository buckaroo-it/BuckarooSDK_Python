# Changelog

All notable changes to this project will be documented in this file.

---

## [Released]

## [0.1.0]
- Initial release.
- Payment methods: iDEAL, iDEAL QR, Apple Pay, Google Pay, Credit Card, PayPal, Bancontact, Belfius, Bizum, Blik, Klarna, Klarna KP, Riverty, In3, Billink, SOFORT, Trustly, EPS, KBC, PayByBank, Payconiq, Przelewy24, SEPA Direct Debit, Swish, TWINT, Alipay, WeChat Pay, MB WAY, Multibanco, Giftcards, Buckaroo Voucher, Knaken, Click to Pay, Wero, External Payment, Transfer.
- Solutions: Subscriptions.
- HTTP strategies: requests and curl, auto-selected via strategy factory.
- HMAC SHA-256 authentication with automatic request signing.
- Observers and logging with stdout, file, and combined destinations plus sensitive-data masking.
- Reply validators and hosted fields OAuth service.
- Builder-pattern fluent API with capability mixins: AuthorizeCapture, EncryptedPay, FastCheckout, InstantRefund, BankTransfer.
