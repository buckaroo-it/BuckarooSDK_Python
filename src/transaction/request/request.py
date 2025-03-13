from typing import Any, Dict

import src.transaction.request.header.default_header as default_header
import src.transaction.request.header.hmac_header as hmac_header
import src.transaction.request.header.culture_header as culture_header
import src.transaction.request.header.channel_header as channel_header
import src.transaction.request.header.software_header as software_header
import src.transaction.request.header.header_interface as header_interface
import src.handlers.config.config_interface as config_interface


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
        self, url: str, data: str, method: str, config: config_interface.ConfigInterface
    ) -> dict:
        internal_headers: header_interface.HeaderInterface = (
            default_header.DefaultHeader(
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json",
                }
            )
        )
        internal_headers = hmac_header.HmacHeader(
            internal_headers, config, url, data, method
        )
        internal_headers = culture_header.CultureHeader(internal_headers, config)
        internal_headers = channel_header.ChannelHeader(internal_headers, config)
        internal_headers = software_header.SoftwareHeader(internal_headers, config)

        complete_internal_headers = internal_headers.get_headers()
        complete_internal_headers.update(self._headers)

        return complete_internal_headers
