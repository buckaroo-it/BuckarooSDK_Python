from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, Self


class ModelInterface(ABC):

    @abstractmethod
    def __getattr__(self, property_name: str) -> Any:
        pass

    @abstractmethod
    def __setattr__(self, property_name: str, value: Any) -> None:
        pass

    @abstractmethod
    def to_dict(self) -> Dict:
        pass

    @abstractmethod
    def set_properties(self, data: Optional[Dict] = None) -> Self:
        pass

    @abstractmethod
    def get_object_vars(self) -> Dict:
        pass

    @abstractmethod
    def service_parameter_key_of(self, property_name: str) -> str:
        pass
