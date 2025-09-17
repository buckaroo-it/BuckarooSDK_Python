
from .exceptions._authentication_error import AuthenticationError


class BuckarooClient(object):

    def __init__(self, store_key: str, secret_key: str) -> None:
        """Initialize the Buckaroo Client class."""

        if store_key is None or not store_key.strip():
            raise AuthenticationError("Store key must be provided")
        
        if secret_key is None or not secret_key.strip():
            raise AuthenticationError("Secret key must be provided")
        
        self.store_key = store_key.strip()
        self.secret_key = secret_key.strip()

        self.payments = PaymentService(self)