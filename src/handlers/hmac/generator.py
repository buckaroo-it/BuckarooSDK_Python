import uuid
import time
import hmac
import hashlib
import base64

import src.handlers.config.config_interface as config_interface
import src.handlers.hmac.hmac as HMAC


class Generator:

    def __init__(
        self,
        config: config_interface.ConfigInterface,
        data: str,
        uri: str,
        method: str = "POST",
    ):
        self._hmac = HMAC.Hmac(
            config,
            data,
            uri,
            str(uuid.uuid4()),
            int(time.time()),
        )
        self._method = method

    @property
    def HMAC(self) -> HMAC.Hmac:
        return self._hmac

    def generate(self) -> str:
        hash_string = f"{self.HMAC.config.website_key()}{self._method}{self.HMAC.uri}{self.HMAC.time}{self.HMAC.nonce}{self.HMAC.base64_data}"

        hash_bytes = hmac.new(
            self.HMAC.config.secret_key().encode("utf-8"),
            hash_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        hmac_value = base64.b64encode(hash_bytes).decode("utf-8")

        return ":".join(
            [
                self.HMAC.config.website_key(),
                hmac_value,
                self.HMAC.nonce,
                str(self.HMAC.time),
            ]
        )
