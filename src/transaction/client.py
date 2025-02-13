from typing import Optional, Dict
from src.config import ConfigInterface
from src.exceptions import BuckarooException
from src.handlers import DefaultLogger, SubjectInterface
from src.resources import endpoints
from .http_client import http_client_factory
from .http_client.http_client_interface import HttpClientInterface
from .response.transaction_response import TransactionResponse
from .response.response import Response
from .request.request import Request


class Client:
    _METHOD_GET = "GET"
    _METHOD_POST = "POST"
    _config: ConfigInterface
    _http_client: HttpClientInterface
    _logger: SubjectInterface

    def __init__(self, config: ConfigInterface):
        self._config = config
        self._http_client = http_client_factory.create_client()
        self._logger = DefaultLogger()
        self._request = Request()

    @property
    def config(self) -> ConfigInterface:
        return self._config

    @config.setter
    def config(self, config: Optional[ConfigInterface] = None) -> None:
        if config:
            self._config = config

        if not self.config:
            raise BuckarooException(
                self.logger,
                "No config has been configured. Please pass your credentials to the constructor or set up a Config object.",
            )

    @property
    def http_client(self) -> HttpClientInterface:
        return self._http_client

    @property
    def logger(self) -> SubjectInterface:
        return self._logger

    @property
    def request(self) -> Request:
        return self._request
    
    def add_header(self, header: dict) -> None:
        self._request.add_header(header)

    def get_transaction_url(self) -> str:
        return self.get_endpoint("json/Transaction/")

    def get_endpoint(self, path: str) -> str:
        base_url = endpoints.LIVE if self.config.is_live_mode() else endpoints.TEST
        return f"{base_url}{path}"

    def get(
        self, end_point: Optional[str] = None
    ) -> TransactionResponse:
        return self.call(method=self._METHOD_GET, end_point=end_point)
    
    def get_with_generic_response(
        self, end_point: Optional[str] = None
    ) -> Response:
        return self.call(method=self._METHOD_GET, end_point=end_point)

    def post(self, data: Optional[Dict] = None) -> TransactionResponse:
        return self.call(self._METHOD_POST, data)

    def data_request(self, data: Optional[Dict] = None) -> TransactionResponse:
        end_point = self.get_endpoint("json/DataRequest/")
        return self.call(self._METHOD_POST, data, end_point)

    def data_batch_request(self, data: Optional[Dict] = None) -> TransactionResponse:
        end_point = self.get_endpoint("json/batch/DataRequests")
        return self.call(self._METHOD_POST, data, end_point)

    def transaction_batch_request(
        self, data: Optional[Dict] = None
    ) -> TransactionResponse:
        end_point = self.get_endpoint("json/batch/Transactions")
        return self.call(self._METHOD_POST, data, end_point)

    def specification(
        self, payment_name: str, data: Optional[Dict] = None, service_version: int = 0
    ) -> TransactionResponse:
        end_point = self.get_endpoint(
            f"json/Transaction/Specification/{payment_name}?serviceVersion={service_version}"
        )
        return self.call(self._METHOD_GET, data, end_point)

    def call(
        self, method: str, data: Optional[Dict], end_point: Optional[str] = None
    ) -> TransactionResponse:
        end_point = end_point or self.get_transaction_url()

        headers = self.request.get_headers(
            end_point, str(data) if data else "", method, self.config
        )
        headers.update(data.get("headers", {}) if data else {})

        self.config.get_logger().info(f"{method} {end_point}")
        self.config.get_logger().info(f"HEADERS: {headers}")

        if data:
            self.config.get_logger().info(f"PAYLOAD: {data}")

        response, decoded_result = self.http_client.call(
            end_point, headers, method, data if data else {}
        )
        response = TransactionResponse(response, decoded_result)

        return response
