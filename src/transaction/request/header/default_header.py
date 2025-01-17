from .header_interface import HeaderInterface


class DefaultHeader(HeaderInterface):
    def __init__(self, headers: dict[str, str]):
        self._headers = headers

    def get_headers(self) -> dict:
        return self._headers or {}
