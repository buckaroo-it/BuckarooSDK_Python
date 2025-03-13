from abc import ABC, abstractmethod
from typing import Optional

import src.models.model_interface as model_interface


class ServiceParameterInterface(model_interface.ModelInterface, ABC):

    @abstractmethod
    def get_group_type(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_group_key(self, key: str) -> Optional[int]:
        pass
