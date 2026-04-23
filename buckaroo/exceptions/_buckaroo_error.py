from typing import Any, Dict, Optional


class BuckarooError(Exception):
    def __init__(
        self,
        message: Optional[str] = None,
        http_body: Optional[str] = None,
        http_status: Optional[int] = None,
        json_body: Optional[object] = None,
        headers: Optional[Dict[str, str]] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        if message is None:
            super().__init__()
        elif http_body is None:
            super().__init__(message)
        else:
            super().__init__(message, http_body)
        self._message = message
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body
        self.headers = headers
        self.code = code
        self.request_id = request_id

    def __str__(self) -> str:
        return self._message or super().__str__()
