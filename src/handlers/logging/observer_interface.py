from abc import ABC, abstractmethod
from typing import List, Dict


class ObserverInterface(ABC):
    @abstractmethod
    def update(self, method: str, message: str, context: List[Dict]):
        pass
