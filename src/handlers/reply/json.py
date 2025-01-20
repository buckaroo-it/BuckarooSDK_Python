from typing import Any, Dict

from src.handlers import Validator
from src.config import ConfigInterface
from .reply_strategy_interface import ReplyStrategyInterface


class Json(ReplyStrategyInterface):

    def __init__(
        self,
        config: ConfigInterface,
        data: Dict[str, Any],
        auth_header: str,
        uri: str,
        method: str = "POST",
    ):
        self.config = config
        self.data = data
        self.auth_header = auth_header
        self.uri = uri
        self.method = method

    def validate(self) -> bool:

        validator = Validator(self.config)
        return validator.validate(self.auth_header, self.uri, self.method, self.data)
