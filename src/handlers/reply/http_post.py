from abc import ABC
from typing import Any, Dict
import hashlib

from .reply_strategy_interface import ReplyStrategyInterface
from src.config import ConfigInterface


class HttpPost(ReplyStrategyInterface):

    def __init__(self, config: ConfigInterface, data: Dict[str, Any]):
        self.config = config
        self.data = data
        self.data = dict(sorted(self.data.items(), key=lambda item: item[0].lower()))

    def validate(self) -> bool:
        acceptable_top_level = ["brq", "add", "cust", "BRQ", "ADD", "CUST"]

        filtered_data = {}
        for key, value in self.data.items():
            if (
                key not in ["brq_signature", "BRQ_SIGNATURE"]
                and key.split("_")[0] in acceptable_top_level
            ):
                filtered_data[key] = value

        data_string = ""
        for key, value in filtered_data.items():
            data_string += f"{key}={html_entity_decode(value)}"

        data_string += self.config.secret_key().strip()

        signature = self.data.get("brq_signature") or self.data.get("BRQ_SIGNATURE")

        if not isinstance(signature, str):
            raise ValueError("Signature must be a string")

        return self._hash_equals(data_string, signature)

    def _hash_equals(self, data_string: str, signature: str) -> bool:
        computed_hash = hashlib.sha1(data_string.encode("utf-8")).hexdigest()
        return computed_hash == signature


def html_entity_decode(value: str) -> str:
    from html import unescape

    return unescape(value)
