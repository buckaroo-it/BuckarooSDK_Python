from abc import ABC, abstractmethod

from src.models import ServiceList

class ServiceListParameterInterface(ABC):
    
    @abstractmethod
    def data(self) -> ServiceList:
        pass