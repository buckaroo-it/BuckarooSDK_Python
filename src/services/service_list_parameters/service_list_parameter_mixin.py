from abc import ABC, abstractmethod
from typing import Any, Optional

from .service_list_parameter_interface import ServiceListParameterInterface
from src.models import ServiceList

class ServiceListParameterMixin(ServiceListParameterInterface):
    @property
    @abstractmethod
    def service_list(self) -> ServiceList:
        pass

    def data(self) -> ServiceList:
        return self.service_list
    
    def _append_parameter(
        self,
        group_key: Optional[int],
        group_type: Optional[str],
        name: str,
        value: Any
    ) -> ServiceListParameterInterface:
        if value is not None:
            self.service_list.append_parameter({
                "Name": name,
                "Value": value,
                "GroupType": "" if group_type is None else group_type,
                "GroupID": "" if group_key is None else group_key,
            })

        return self