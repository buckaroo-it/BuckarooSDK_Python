from abc import ABC, abstractmethod
from typing import List
from src.handlers import SubjectInterface


class ConfigInterface(ABC):
    @abstractmethod
    def website_key(self) -> str:
        pass

    @abstractmethod
    def secret_key(self) -> str:
        pass

    @abstractmethod
    def is_live_mode(self) -> bool:
        pass

    @abstractmethod
    def mode(self) -> str:
        pass

    @abstractmethod
    def currency(self) -> str:
        pass

    @abstractmethod
    def return_url(self) -> str:
        pass

    @abstractmethod
    def return_url_cancel(self) -> str:
        pass

    @abstractmethod
    def push_url(self) -> str:
        pass

    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    def platform_version(self) -> str:
        pass

    @abstractmethod
    def module_supplier(self) -> str:
        pass

    @abstractmethod
    def module_name(self) -> str:
        pass

    @abstractmethod
    def module_version(self) -> str:
        pass

    @abstractmethod
    def culture(self) -> str:
        pass

    @abstractmethod
    def channel(self) -> str:
        pass

    @abstractmethod
    def set_logger(self, logger: SubjectInterface) -> None:
        pass

    @abstractmethod
    def get_logger(self) -> SubjectInterface:
        pass
