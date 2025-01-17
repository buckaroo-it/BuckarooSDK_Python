from .header_interface import HeaderInterface
from src.config import ConfigInterface
import json


class SoftwareHeader(HeaderInterface):

    def __init__(self, header: HeaderInterface, config: ConfigInterface):
        self._header = header
        self._config = config

    def get_headers(self) -> dict:
        headers = self._header.get_headers()

        software_info = {
            "PlatformName": self._config.platform_name(),
            "PlatformVersion": self._config.platform_version(),
            "ModuleSupplier": self._config.module_supplier(),
            "ModuleName": self._config.module_name(),
            "ModuleVersion": self._config.module_version(),
        }

        headers["Software"] = json.dumps(software_info)

        return headers
