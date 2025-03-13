from typing import Any, Dict

import src.handlers.hmac.validator as hmacValidator
import src.handlers.config.config_interface as config_interface
import src.handlers.reply.reply_strategy_interface as reply_strategy_interface


class Json(reply_strategy_interface.ReplyStrategyInterface):

    def __init__(
        self,
        config: config_interface.ConfigInterface,
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

        validator = hmacValidator.Validator(self.config)
        return validator.validate(self.auth_header, self.uri, self.method, self.data)
