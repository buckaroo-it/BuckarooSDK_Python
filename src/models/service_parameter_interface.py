from abc import ABC, abstractmethod
from typing import Optional


class ServiceParameterInterface(ABC):

    @abstractmethod
    def get_group_type(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_group_key(self, key: str, key_count: int = 0) -> Optional[int]:
        pass
