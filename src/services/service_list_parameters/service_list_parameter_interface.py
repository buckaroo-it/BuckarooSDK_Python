from abc import ABC, abstractmethod

import src.models.service_list as service_list


class ServiceListParameterInterface(ABC):

    @abstractmethod
    def data(self) -> "service_list.ServiceList":
        pass
