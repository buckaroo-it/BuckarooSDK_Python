from typing import List, Union
from dotenv import load_dotenv
import os

import src.handlers.logging.observers.error_reporter as error_reporter
import src.handlers.logging.observers.logger_reporter as logger_reporter
import src.handlers.logging.observer_interface as observer_interface
import src.handlers.logging.subject_interface as subject_interface

load_dotenv()


class DefaultLogger(subject_interface.SubjectInterface):
    def __init__(self) -> None:
        self._observers: List[observer_interface.ObserverInterface] = []

        if os.getenv("BPE_LOG") == "true":
            self.attach(logger_reporter.LoggerReporter())

        if os.getenv("BPE_REPORT_ERROR") == "true":
            self.attach(error_reporter.ErrorReporter())

    def attach(
        self,
        new_observer_interface: Union[
            observer_interface.ObserverInterface,
            List[observer_interface.ObserverInterface],
        ],
    ) -> None:
        if isinstance(new_observer_interface, list):
            for obs_interface in new_observer_interface:
                self.attach(obs_interface)
            return

        if isinstance(new_observer_interface, observer_interface.ObserverInterface):
            self._observers.append(new_observer_interface)

    def detach(self, ObserverInterface: observer_interface.ObserverInterface) -> None:
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
