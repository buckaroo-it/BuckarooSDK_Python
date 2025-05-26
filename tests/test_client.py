import time

from buckaroo.api.client import Client


def test_client_website_secret_key():
    """Test the Client class with website secret key."""
    client = Client()

    client.config.set_website_key("websitekey_123")
    assert client.config.website_key == "websitekey_123"

    client.config.set_secret_key("secretkey_123")
    assert client.config.secret_key == "secretkey_123"