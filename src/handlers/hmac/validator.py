import base64
import hmac
import hashlib
from typing import Any

import src.handlers.config.config_interface as config_interface
import src.exceptions.buckaroo_exception as buckaroo_exception
import src.handlers.hmac.hmac as HMAC


class Validator:
    def __init__(self, config: config_interface.ConfigInterface):
        self._hmac = HMAC.Hmac(config, "", "", "", "")
        self._hash = ""

    @property
    def HMAC(self) -> HMAC.Hmac:
        return self._hmac

    def validate(self, header: str, uri: str, method: str, data: Any) -> bool:
        header_parts = header.split(":")
        provided_hash = header_parts[1]

        self.HMAC.uri = uri
        self.HMAC.nonce = header_parts[2]
        self.HMAC.time = header_parts[3]

        self.HMAC.base64_data = data

        hmac_string = f"{self.HMAC.config.website_key()}{method}{self.HMAC.uri}{self.HMAC.time}{self.HMAC.nonce}{self.HMAC.base64_data}"

        hash_bytes = hmac.new(
            self.HMAC.config.secret_key().encode("utf-8"),
            hmac_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        self._hash = base64.b64encode(hash_bytes).decode("utf-8")

        return provided_hash == self._hash

    def validate_or_fail(self, header: str, uri: str, method: str, data: Any) -> bool:
        if self.validate(header, uri, method, data):
            return True

        raise buckaroo_exception.BuckarooException("HMAC validation failed.")
