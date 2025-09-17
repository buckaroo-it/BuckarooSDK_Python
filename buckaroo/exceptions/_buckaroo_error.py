from typing import Dict, Optional, Union, cast

class BuckarooError(Exception):
    _message: Optional[str]
    http_body: Optional[str]
    http_status: Optional[int]
    json_body: Optional[object]
    headers: Optional[Dict[str, str]]
    code: Optional[str]
    request_id: Optional[str]
    error: Optional["ErrorObject"]
