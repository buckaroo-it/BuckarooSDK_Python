"""
Transaction execution service for Buckaroo SDK.

Centralises the logic for posting requests to the Buckaroo API so that
builders only need to construct the request payload, not manage HTTP concerns.
"""

from typing import Dict, Any

try:
    from typing import Protocol, runtime_checkable
except ImportError:
    from typing_extensions import Protocol, runtime_checkable  # type: ignore[assignment]

from ..models.payment_response import PaymentResponse


@runtime_checkable
class ITransactionExecutor(Protocol):
    """Protocol that any transaction executor must satisfy.

    Builders depend on this abstraction, not on ``TransactionExecutor`` directly,
    so tests can inject a mock without touching the network.
    """

    def post_transaction(self, request_data: Dict[str, Any]) -> PaymentResponse:
        """Post a standard payment transaction."""
        ...

    def post_data_request(self, request_data: Dict[str, Any]) -> PaymentResponse:
        """Post a data request (subscriptions, Klarna KP, etc.)."""
        ...


class TransactionExecutor:
    """
    Handles posting payment requests to the Buckaroo API.

    Builders hold a reference to this executor and delegate all HTTP calls
    to it, keeping the HTTP concern out of the builder layer.
    """

    _TRANSACTION_ENDPOINT = "/json/transaction"
    _DATA_REQUEST_ENDPOINT = "/json/DataRequest"

    def __init__(self, client) -> None:
        """
        Args:
            client: BuckarooClient instance that owns the http_client.
        """
        self._client = client

    def post(self, endpoint: str, request_data: Dict[str, Any]) -> PaymentResponse:
        """Post a request to the given Buckaroo endpoint.

        Args:
            endpoint: API path, e.g. '/json/transaction'
            request_data: Serialised payment request dictionary

        Returns:
            PaymentResponse: Structured response object (never None)
        """
        response = self._client.http_client.post(endpoint, request_data)
        if response is None:
            return PaymentResponse({})
        return PaymentResponse(response.to_dict())

    def post_transaction(self, request_data: Dict[str, Any]) -> PaymentResponse:
        """Post a standard payment transaction."""
        return self.post(self._TRANSACTION_ENDPOINT, request_data)

    def post_data_request(self, request_data: Dict[str, Any]) -> PaymentResponse:
        """Post a data request (used for subscriptions, Klarna KP, etc.)."""
        return self.post(self._DATA_REQUEST_ENDPOINT, request_data)
