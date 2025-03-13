import logging
from typing import List, Dict
import src.handlers.logging.observer_interface as observer_interface


class LoggerReporter(observer_interface.ObserverInterface):
    def __init__(self):
        self.log = logging.getLogger("Buckaroo log")
        self.log.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler.setFormatter(formatter)

        self.log.addHandler(stream_handler)

    def update(self, method: str, message: str, context: List[Dict] = []) -> None:
        log_method = getattr(self.log, method, None)
        if log_method:
            log_method(message, *context)
