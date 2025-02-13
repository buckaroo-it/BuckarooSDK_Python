from typing import Any, Dict

from .header.default_header import DefaultHeader
from .header.hmac_header import HmacHeader
from .header.culture_header import CultureHeader
from .header.channel_header import ChannelHeader
from .header.software_header import SoftwareHeader
from .header.header_interface import HeaderInterface
from src.config import ConfigInterface


class Request:
    _headers: Dict[str, Any] = {}
    _body: Dict[str, Any] = {}

    def __init__(self, headers: Dict[str, Any] = {}, body: Dict[str, Any] = {}):
        self._headers = headers
        self._body = body

    @property
    def headers(self) -> Dict[str, Any]:
        return self._headers

    @property
    def body(self) -> Dict[str, Any]:
        return self._body

    def add_header(self, header: Dict[str, Any]) -> None:
        self._headers.update(header)

    def get_headers(
        self, url: str, data: str, method: str, config: ConfigInterface
    ) -> dict:
        internal_headers: HeaderInterface = DefaultHeader(
            {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            }
        )
        internal_headers = HmacHeader(internal_headers, config, url, data, method)
        internal_headers = CultureHeader(internal_headers, config)
        internal_headers = ChannelHeader(internal_headers, config)
        internal_headers = SoftwareHeader(internal_headers, config)

        complete_internal_headers = internal_headers.get_headers()
        complete_internal_headers.update(self._headers)

        return complete_internal_headers
