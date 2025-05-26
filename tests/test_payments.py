import pytest

PAYMENT_ID = "tr_7UhSN1zuXS"


def test_create_ideal_payment(client, response):
    """Create a new iDEAL payment."""
    response.post("https://api.buckaroo.com/payments", "payment_single")

    payment = client.payments.ideal(
        {
            "amount": {
                "currency": "EUR", 
                "value": "10.00"
            },
            "description": "Order #12345",
            "redirectUrl": "https://webshop.example.org/order/12345/",
            "cancelUrl": "https://webshop.example.org/payment-canceled",
            "webhookUrl": "https://webshop.example.org/payments/webhook/",
            "method": "ideal",
        }
    ).create()

    assert payment.id == PAYMENT_ID