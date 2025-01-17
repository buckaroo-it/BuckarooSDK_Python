from typing import Optional
from urllib.parse import urlparse, urlencode
import json
import hashlib
import base64
from src.config import ConfigInterface
from typing import Union


class Hmac:
    def __init__(
        self,
        config: ConfigInterface,
        base64_data: str = "",
        uri: str = "",
        nonce: str = "",
        time: Union[int, str] = 0,
    ) -> None:
        self._config = config
        self._base64_data = base64_data
        self._uri = uri
        self._nonce = nonce
        self._time = time

    @property
    def config(self) -> ConfigInterface:
        return self._config

    @property
    def base64_data(self) -> str:
        return self._base64_data

    @base64_data.setter
    def base64_data(self, value: Optional[dict]) -> None:
        if value:
            self._base64_data = self.generate_base64_data(value)
        self._base64_data = ""

    @property
    def uri(self) -> str:
        return self._uri

    @uri.setter
    def uri(self, value: str) -> None:
        if value:
            self._uri = self.generate_uri(value)
        self._uri = value

    @property
    def nonce(self) -> str:
        return self._nonce

    @nonce.setter
    def nonce(self, value: str) -> None:
        self._nonce = value

    @property
    def time(self) -> Union[int, str]:
        return self._time

    @time.setter
    def time(self, value: Union[int, str]) -> None:
        self._time = value

    def generate_uri(self, uri: str) -> str:
        if uri:
            parsed = urlparse(uri)
            uri = parsed.netloc + parsed.path
            return urlencode({"": uri}).lstrip("=").lower()
        return ""

    def generate_base64_data(self, data=None) -> str:
        if data:
            if isinstance(data, dict):
                data = json.dumps(data, ensure_ascii=False)

            md5_hash = hashlib.md5(data.encode("utf-8")).digest()

            return base64.b64encode(md5_hash).decode("utf-8")

        return self.base64_data
