from typing import List, Union
from .observer_interface import ObserverInterface
from .subject_interface import SubjectInterface
from dotenv import load_dotenv
import os
from .observers.error_reporter import ErrorReporter
from .observers.logger_reporter import LoggerReporter

load_dotenv()


class DefaultLogger(SubjectInterface):
    def __init__(self) -> None:
        self._observers: List[ObserverInterface] = []

        if os.getenv("BPE_LOG") == "true":
            self.attach(LoggerReporter())

        if os.getenv("BPE_REPORT_ERROR") == "true":
            self.attach(ErrorReporter())

    def attach(
        self, observer_interface: Union[ObserverInterface, List[ObserverInterface]]
    ) -> None:
        if isinstance(observer_interface, list):
            for obs_interface in observer_interface:
                self.attach(obs_interface)
            return

        if isinstance(observer_interface, ObserverInterface):
            self._observers.append(observer_interface)

    def detach(self, ObserverInterface: ObserverInterface) -> None:
        self._observers = [
            o for o in self._observers if not isinstance(o, type(ObserverInterface))
        ]

    def notify(self, method: str, message: str, context: List[dict] = []) -> None:
        for observer_interface in self._observers:
            observer_interface.update(method, message, context)

    def emergency(self, message: str, context: List[dict] = []) -> None:
        self.notify("emergency", message, context)

    def alert(self, message: str, context: List[dict] = []) -> None:
        self.notify("alert", message, context)

    def critical(self, message: str, context: List[dict] = []) -> None:
        self.notify("critical", message, context)

    def error(self, message: str, context: List[dict] = []) -> None:
        self.notify("error", message, context)

    def warning(self, message: str, context: List[dict] = []) -> None:
        self.notify("warning", message, context)

    def notice(self, message: str, context: List[dict] = []) -> None:
        self.notify("notice", message, context)

    def info(self, message: str, context: List[dict] = []) -> None:
        self.notify("info", message, context)

    def debug(self, message: str, context: List[dict] = []) -> None:
        if os.getenv("BPE_DEBUG") == "true":
            self.notify("debug", message, context)

    def log(self, message: str, context: List[dict] = []) -> None:
        self.notify("log", message, context)
