from .client import Client
from .response.response import Response
from .response.transaction_response import TransactionResponse

class TransactionService:
    def __init__(self, client: Client, transaction_key: str):
        self.transaction_key = transaction_key
        self.client = client

    def status(self) -> TransactionResponse:
        endpoint = f"json/Transaction/Status/{self.transaction_key}"
        return self.client.get(self.client.get_endpoint(endpoint))

    def refund_info(self) -> Response:
        endpoint = f"json/Transaction/RefundInfo/{self.transaction_key}"
        return self.client.get_with_generic_response(self.client.get_endpoint(endpoint))

    def cancel_info(self) -> Response:
        endpoint = f"json/Transaction/Cancel/{self.transaction_key}"
        return self.client.get_with_generic_response(self.client.get_endpoint(endpoint))