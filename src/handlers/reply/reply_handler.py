import json
from typing import Self

import src.handlers.reply.http_post as http_post
import src.handlers.reply.json as Json
import src.handlers.config.config_interface as config_interface
import src.handlers.reply.reply_strategy_interface as reply_strategy_interface


class ReplyHandler:
    strategy: reply_strategy_interface.ReplyStrategyInterface

    def __init__(
        self,
        config: config_interface.ConfigInterface,
        data: dict,
        auth_header: str,
        uri: str,
    ):
        self.config = config
        self.data = data
        self.auth_header = auth_header
        self.uri = uri
        self._is_valid = False

    def validate(self) -> Self:
        self.set_strategy()
        self._is_valid = self.strategy.validate()
        return self

    def set_strategy(self) -> None:
        if isinstance(self.data, str):
            self.data = json.loads(self.data)

        if self.contains("Transaction", self.data) and self.auth_header and self.uri:
            self.strategy = Json.Json(
                self.config, self.data, self.auth_header, self.uri
            )
            return

        if self.contains("brq_", self.data) or self.contains("BRQ_", self.data):
            self.strategy = http_post.HttpPost(self.config, self.data)
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
