import src.handlers.config.config_interface as config_interface
import src.handlers.hmac.generator as generator
import src.transaction.request.header.header_interface as header_interface


class HmacHeader(header_interface.HeaderInterface):
    _hmac_generator: generator.Generator

    def __init__(
        self,
        header: header_interface.HeaderInterface,
        config: config_interface.ConfigInterface,
        request_uri: str,
        data: str,
        http_method: str,
    ):
        self._header = header
        self._config = config
        self._request_uri = request_uri
        self._data = data
        self._http_method = http_method
        self._hmac_generator = generator.Generator(
            config, data, request_uri, http_method
        )

    def get_headers(self) -> dict:
        headers = self._header.get_headers()

        headers["Authorization: hmac"] = self._hmac_generator.generate()

        return headers
