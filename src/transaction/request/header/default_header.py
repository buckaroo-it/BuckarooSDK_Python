import src.transaction.request.header.header_interface as header_interface


class DefaultHeader(header_interface.HeaderInterface):
    def __init__(self, headers: dict[str, str]):
        self._headers = headers

    def get_headers(self) -> dict:
        return self._headers or {}
