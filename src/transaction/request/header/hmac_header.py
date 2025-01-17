from .header_interface import HeaderInterface
from src.config import ConfigInterface
from src.handlers import Generator


class HmacHeader(HeaderInterface):
    _hmac_generator: Generator

    def __init__(
        self,
        header: HeaderInterface,
        config: ConfigInterface,
        request_uri: str,
        data: str,
        http_method: str,
    ):
        self._header = header
        self._config = config
        self._request_uri = request_uri
        self._data = data
        self._http_method = http_method
        self._hmac_generator = Generator(config, data, request_uri, http_method)

    def get_headers(self) -> dict:
        headers = self._header.get_headers()

        headers["Authorization: hmac"] = self._hmac_generator.generate()

        return headers
