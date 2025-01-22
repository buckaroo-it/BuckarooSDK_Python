import json
from typing import Self

from .http_post import HttpPost
from .json import Json
from src.config import ConfigInterface
from src.handlers import ReplyStrategyInterface


class ReplyHandler:
    def __init__(self, config: ConfigInterface, data: dict, auth_header: str, uri: str):
        self.config = config
        self.data = data
        self.auth_header = auth_header
        self.uri = uri
        self._is_valid = False
        self.strategy: ReplyStrategyInterface

    def validate(self) -> Self:
        self.set_strategy()
        self._is_valid = self.strategy.validate()
        return self

    def set_strategy(self) -> None:
        if isinstance(self.data, str):
            self.data = json.loads(self.data)

        if self.contains("Transaction", self.data) and self.auth_header and self.uri:
            self.strategy = Json(self.config, self.data, self.auth_header, self.uri)
            return

        if self.contains("brq_", self.data) or self.contains("BRQ_", self.data):
            self.strategy = HttpPost(self.config, self.data)
            return

        raise Exception("No reply handler strategy applied.")

    def contains(self, needle, data, strict=False) -> bool:
        for key in data.keys():
            if strict and key == needle:
                return True
            if not strict and needle in key:
                return True
        return False

    @property
    def is_valid(self) -> bool:
        return self._is_valid
