from typing import Optional
import json

import src.exceptions.buckaroo_exception as buckaroo_exception
import src.resources.constants.endpoints as endpoints
import src.handlers.config.config_interface as config_interface
import src.handlers.logging.default_logger as default_logger
import src.handlers.logging.subject_interface as subject_interface
import src.transaction.request.transaction_request as transaction_request
import src.transaction.request.request as request
import src.transaction.response.response as response
import src.transaction.response.transaction_response as transaction_response
import src.transaction.http_client.http_client_interface as http_client_interface
import src.transaction.http_client.http_client_factory as http_client_factory
import src.transaction.http_client.http_client_interface as http_client_interface


class Client:
    _METHOD_GET = "GET"
    _METHOD_POST = "POST"
    _config: config_interface.ConfigInterface
    _http_client: http_client_interface.HttpClientInterface
    _logger: subject_interface.SubjectInterface

    def __init__(self, config: config_interface.ConfigInterface):
        self._config = config
        self._http_client = http_client_factory.create_client()
        self._logger = default_logger.DefaultLogger()
        self._request = request.Request()

    @property
    def config(self) -> config_interface.ConfigInterface:
        return self._config

    @config.setter
    def config(self, config: Optional[config_interface.ConfigInterface] = None) -> None:
        if config:
            self._config = config

        if not self.config:
            raise buckaroo_exception.BuckarooException(
                self.logger,
                "No config has been configured. Please pass your credentials to the constructor or set up a Config object.",
            )

    @property
    def http_client(self) -> http_client_interface.HttpClientInterface:
        return self._http_client

    @property
    def logger(self) -> subject_interface.SubjectInterface:
        return self._logger

    @property
    def request(self) -> request.Request:
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
    ) -> transaction_response.TransactionResponse:
        return self._call(method=self._METHOD_GET, data=None, end_point=end_point)

    def get_with_generic_response(
        self, end_point: Optional[str] = None
    ) -> response.Response:
        return self._call(method=self._METHOD_GET, data=None, end_point=end_point)

    def post(
        self, data: transaction_request.TransactionRequest
    ) -> transaction_response.TransactionResponse:
        return self._call(self._METHOD_POST, data)

    def data_request(
        self, data: transaction_request.TransactionRequest
    ) -> transaction_response.TransactionResponse:
        end_point = self.get_endpoint("json/DataRequest/")
        return self._call(self._METHOD_POST, data, end_point)

    def data_batch_request(
        self, data: transaction_request.TransactionRequest
    ) -> transaction_response.TransactionResponse:
        end_point = self.get_endpoint("json/batch/DataRequests")
        return self._call(self._METHOD_POST, data, end_point)

    def transaction_batch_request(
        self, data: transaction_request.TransactionRequest
    ) -> transaction_response.TransactionResponse:
        end_point = self.get_endpoint("json/batch/Transactions")
        return self._call(self._METHOD_POST, data, end_point)

    def specification(
        self,
        payment_name: str,
        data: transaction_request.TransactionRequest,
        service_version: int = 0,
    ) -> transaction_response.TransactionResponse:
        end_point = self.get_endpoint(
            f"json/Transaction/Specification/{payment_name}?serviceVersion={service_version}"
        )
        return self._call(self._METHOD_GET, data, end_point)

    def _call(
        self,
        method: str,
        data: transaction_request.TransactionRequest | None,
        end_point: Optional[str] = None,
    ) -> transaction_response.TransactionResponse:
        end_point = end_point or self.get_transaction_url()

        headers = self.request.get_headers(
            end_point,
            method=method,
            data=data.get_data_as_json() if data else "",
            config=self.config,
        )

        if data:
            headers.update(json.loads(data.get_data_as_json()))

        self.config.get_logger().info(f"{method} {end_point}")
        self.config.get_logger().info(f"HEADERS: {headers}")

        if data:
            self.config.get_logger().info(f"PAYLOAD: {data}")

        response, decoded_result = self.http_client.call(
            end_point, headers, method, data.get_data_as_json() if data else ""
        )
        response = transaction_response.TransactionResponse(response, decoded_result)

        return response
