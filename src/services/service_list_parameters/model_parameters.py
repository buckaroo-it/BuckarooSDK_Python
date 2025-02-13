from typing import Optional

from src.models import ServiceList
from .service_list_parameter_mixin import ServiceListParameterMixin
from .service_list_parameter_interface import ServiceListParameterInterface
from src.models.model_interface import ModelInterface
from src.models.service_parameter_interface import ServiceParameterInterface

class ModelParameters(ServiceListParameterMixin):
    def __init__(self, service_list_parameter: ServiceListParameterInterface, model: ModelInterface, group_type: Optional[str] = '', group_key: Optional[int] = None):
        self._model = model
        self._group_type = group_type
        self._group_key = group_key
        self._service_list_parameter = service_list_parameter
        self._service_list = self._service_list_parameter.data()
    
    @property
    def service_list(self) -> ServiceList:
        return self._service_list
    
    @property
    def model(self) -> ModelInterface:
        return self._model
    
    def data(self):
        for key, value in self.model.to_dict().items():
            if not isinstance(value, list):  
                self.append_parameter(
                    self.__group_key(key),  
                    self.__group_type(key), 
                    self.model.service_parameter_key_of(key),
                    value
                )
        return self.service_list

    def __group_key(self, key):
        if isinstance(self.model, ServiceParameterInterface) and not self._group_key:
            return self.model.get_group_key(key)
        return self.group_key

    def __group_type(self, key):
        if isinstance(self.model, ServiceListParameterInterface) and not self._group_type:
            return self.model.get_group_type(key)
        return self.group_type
    
