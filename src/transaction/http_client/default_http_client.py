from .http_client_interface import HttpClientInterface
import httpx
from typing import Any, Mapping
from src.exceptions import HttpxException


class DefaultHttpClient(HttpClientInterface):
    def __init__(self):
        self._client = httpx

    def call(
        self, url: str, headers: dict, method: str, data: Mapping[str, Any] | None
    ) -> Any:
        try:
            response = self._client.request(method, url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HttpxException(f"HTTP error occurred: {e}")
        except httpx.RequestError as e:
            raise HttpxException(f"Request error occurred: {e}")
        except Exception as e:
            raise HttpxException(f"An unexpected error occurred: {e}")
