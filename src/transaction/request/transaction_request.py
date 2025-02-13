from typing import Dict, Any, Self
import os

from .request import Request
from src.models import ModelInterface

class TransactionRequest(Request):
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._data["ClientUserAgent"] = self.get_client_user_agent()

    def set_payload(self, model: ModelInterface) -> Self:
        for key, value in model.to_dict().items():
            self.data[model.service_parameter_key_of(key)] = value
        return self

    def set_data(self, key: str, value: Any) -> Self:
        self.data[key] = value
        return self

    def get_data(self) -> Dict[str, Any]:
        return self.data

    def get_services(self) -> Dict[str, Any]:
        if "Services" not in self.data:
            return {}
        return self.data["Services"]
    
    @staticmethod
    def get_client_user_agent() -> str:
        return os.getenv("HTTP_USER_AGENT", "")