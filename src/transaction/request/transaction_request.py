from typing import Dict, Any, Self
import os
import json

import src.models.model_interface as model_interface
import src.models.service_list as service_list
import src.transaction.request.request as request


class TransactionRequest(request.Request):
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._data["ClientUserAgent"] = self.get_client_user_agent()

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    def set_payload(self, model: model_interface.ModelInterface) -> Self:
        for key, value in model.to_dict().items():
            self.data[model.service_parameter_key_of(key)] = value
        return self

    def set_data(self, key: str, value: Any) -> Self:
        self.data[key] = value
        return self

    def get_data(self) -> Dict[str, Any]:
        return self.data

    def get_data_as_json(self) -> str:
        data = self.get_data()
        return json.dumps(self.get_data())

    def set_services(self, service_list: service_list.ServiceList) -> None:
        if "Services" in self.data:
            self.data["Services"].extend(service_list)
        else:
            self.data["Services"] = service_list

    @staticmethod
    def get_client_user_agent() -> str:
        return os.getenv("HTTP_USER_AGENT", "")
