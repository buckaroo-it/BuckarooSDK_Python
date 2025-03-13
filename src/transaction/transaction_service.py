import src.transaction.client as client
import src.transaction.response.response as response
import src.transaction.response.transaction_response as transaction_response


class TransactionService:
    def __init__(self, client: client.Client, transaction_key: str):
        self.transaction_key = transaction_key
        self.client = client

    def status(self) -> transaction_response.TransactionResponse:
        endpoint = f"json/Transaction/Status/{self.transaction_key}"
        return self.client.get(self.client.get_endpoint(endpoint))

    def refund_info(self) -> response.Response:
        endpoint = f"json/Transaction/RefundInfo/{self.transaction_key}"
        return self.client.get_with_generic_response(self.client.get_endpoint(endpoint))

    def cancel_info(self) -> response.Response:
        endpoint = f"json/Transaction/Cancel/{self.transaction_key}"
        return self.client.get_with_generic_response(self.client.get_endpoint(endpoint))
