from abc import ABC, abstractmethod


class HeaderInterface(ABC):
    @abstractmethod
    def get_headers(self) -> dict:
        pass
