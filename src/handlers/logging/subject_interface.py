from abc import ABC, abstractmethod
from typing import List, Dict

from .observer_interface import ObserverInterface


class SubjectInterface(ABC):
    @abstractmethod
    def attach(self, observer: ObserverInterface) -> None:
        pass

    @abstractmethod
    def detach(self, observer: ObserverInterface) -> None:
        pass

    @abstractmethod
    def notify(self, method: str, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def emergency(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def alert(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def critical(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def error(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def notice(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def info(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def debug(self, message: str, context: List[Dict] = []) -> None:
        pass

    @abstractmethod
    def log(self, message: str, context: List[Dict] = []) -> None:
        pass
