import requests
from typing import Any

import src.transaction.http_client.http_client_interface as http_client_interface


class DefaultHttpClient(http_client_interface.HttpClientInterface):
    def call(self, url: str, headers: dict, method: str, data: str | None) -> Any:
        try:
            response = requests.request(method, url, headers=headers, data=data)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to call {url}") from e
