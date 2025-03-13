from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Self

class ServiceListInterface(ABC):
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def append_parameter(self, value: Any, key: Optional[str] = None) -> Self:
        pass