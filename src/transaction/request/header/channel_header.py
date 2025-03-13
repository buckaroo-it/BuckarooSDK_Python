import src.transaction.request.header.header_interface as header_interface
import src.handlers.config.config_interface as config_interface


class ChannelHeader(header_interface.HeaderInterface):
    def __init__(
        self,
        header: header_interface.HeaderInterface,
        config: config_interface.ConfigInterface,
    ):
        self._header = header
        self._config = config

    def get_headers(self) -> dict:
        headers = self._header.get_headers()
        headers["channel"] = f"Channel{self._config.channel()}"

        return headers
