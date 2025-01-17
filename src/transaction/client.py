from typing import Optional, Dict
from src.config import ConfigInterface
from src.exceptions import BuckarooException
from src.handlers import DefaultLogger, SubjectInterface
from src.resources import endpoints
from .request.header.default_header import DefaultHeader
from .request.header.hmac_header import HmacHeader
from .request.header.culture_header import CultureHeader
from .request.header.channel_header import ChannelHeader
from .request.header.software_header import SoftwareHeader
from .http_client import http_client_factory
from .http_client.http_client_interface import HttpClientInterface
from .response.transaction_response import TransactionResponse
from .request.header.header_interface import HeaderInterface


class Client:
    METHOD_GET = "GET"
    METHOD_POST = "POST"
    _config: ConfigInterface
    _http_client: HttpClientInterface
    _logger: SubjectInterface
    _headers: HeaderInterface
    _initial_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
    }

    def __init__(self, config: ConfigInterface):
        self._config = config
        self._http_client = http_client_factory.create_client()
        self._logger = DefaultLogger()

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
    def http_client(self):
        return self._http_client

    @property
    def logger(self):
        return self._logger

    def get_transaction_url(self) -> str:
        return self.get_endpoint("json/Transaction/")

    def get_endpoint(self, path: str) -> str:
        base_url = endpoints.LIVE if self.config.is_live_mode() else endpoints.TEST
        return f"{base_url}{path}"

    def get(
        self, data: Optional[Dict] = None, end_point: Optional[str] = None
    ) -> TransactionResponse:
        return self.call(self.METHOD_GET, data, end_point)

    def post(self, data: Optional[Dict] = None) -> TransactionResponse:
        return self.call(self.METHOD_POST, data)

    def data_request(self, data: Optional[Dict] = None) -> TransactionResponse:
        end_point = self.get_endpoint("json/DataRequest/")
        return self.call(self.METHOD_POST, data, end_point)

    def data_batch_request(self, data: Optional[Dict] = None) -> TransactionResponse:
        end_point = self.get_endpoint("json/batch/DataRequests")
        return self.call(self.METHOD_POST, data, end_point)

    def transaction_batch_request(
        self, data: Optional[Dict] = None
    ) -> TransactionResponse:
        end_point = self.get_endpoint("json/batch/Transactions")
        return self.call(self.METHOD_POST, data, end_point)

    def specification(
        self, payment_name: str, data: Optional[Dict] = None, service_version: int = 0
    ) -> TransactionResponse:
        end_point = self.get_endpoint(
            f"json/Transaction/Specification/{payment_name}?serviceVersion={service_version}"
        )
        return self.call(self.METHOD_GET, data, end_point)

    def call(
        self, method: str, data: Optional[Dict], end_point: Optional[str] = None
    ) -> TransactionResponse:
        end_point = end_point or self.get_transaction_url()

        headers = self.get_headers(end_point, str(data) if data else "", method)
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

    def get_headers(self, url: str, data: str, method: str) -> dict:
        self._headers = DefaultHeader(self._initial_headers)
        self._headers = HmacHeader(self._headers, self.config, url, data, method)
        self._headers = CultureHeader(self._headers, self.config)
        self._headers = ChannelHeader(self._headers, self.config)
        self._headers = SoftwareHeader(self._headers, self.config)

        return self._headers.get_headers()
