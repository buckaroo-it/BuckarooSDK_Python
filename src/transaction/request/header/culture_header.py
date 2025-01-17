from .header_interface import HeaderInterface
from src.config import ConfigInterface


class CultureHeader(HeaderInterface):
    def __init__(self, header: HeaderInterface, config: ConfigInterface):
        self._header = header
        self._config = config

    def get_headers(self) -> dict:
        headers = self._header.get_headers()
        headers["culture"] = f"Culture{self._config.culture()}"

        return headers
