from src.models import ServiceList
from .service_list_parameter_mixin import ServiceListParameterMixin

class DefaultParameters(ServiceListParameterMixin):
    def __init__(self, service_list: ServiceList):
        self._service_list = service_list
    
    @property
    def service_list(self) -> ServiceList:
        return self._service_list