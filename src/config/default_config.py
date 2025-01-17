from typing import Optional, List
from dotenv import load_dotenv
import os
from src.config import ConfigInterface
from src.handlers import SubjectInterface, DefaultLogger

load_dotenv()


class DefaultConfig(ConfigInterface):
    def __init__(
        self,
        website_key: str,
        secret_key: str,
        mode: Optional[str] = None,
        currency: Optional[str] = None,
        return_url: Optional[str] = None,
        return_url_cancel: Optional[str] = None,
        push_url: Optional[str] = None,
        platform_name: Optional[str] = None,
        platform_version: Optional[str] = None,
        module_supplier: Optional[str] = None,
        module_name: Optional[str] = None,
        module_version: Optional[str] = None,
        culture: Optional[str] = None,
        channel: Optional[str] = None,
        logger: Optional[SubjectInterface] = None,
    ) -> None:
        self.LIVE_MODE = "live"
        self.TEST_MODE = "test"

        self._website_key = website_key
        self._secret_key = secret_key

        self._mode = os.getenv("BPE_MODE", mode or self.TEST_MODE)
        self._currency = os.getenv("BPE_CURRENCY_CODE", currency or "EUR")
        self._return_url = os.getenv("BPE_RETURN_URL", return_url or "")
        self._return_url_cancel = os.getenv(
            "BPE_RETURN_URL_CANCEL", return_url_cancel or ""
        )
        self._push_url = os.getenv("BPE_PUSH_URL", push_url or "")
        self._platform_name = os.getenv(
            "PlatformName", platform_name or "Default Platform"
        )
        self._platform_version = os.getenv(
            "PlatformVersion", platform_version or "1.0.0"
        )
        self._module_supplier = os.getenv(
            "ModuleSupplier", module_supplier or "Default Supplier"
        )
        self._module_name = os.getenv("ModuleName", module_name or "Default Module")
        self._module_version = os.getenv("ModuleVersion", module_version or "1.0.0")
        self._culture = os.getenv("Culture", culture or "")
        self._channel = os.getenv("Channel", channel or "")
        self._logger = logger or DefaultLogger()

    def website_key(self) -> str:
        return self._website_key

    def secret_key(self) -> str:
        return self._secret_key

    def is_live_mode(self) -> bool:
        return self._mode == self.LIVE_MODE

    def mode(self) -> str:
        return self._mode

    def currency(self) -> str:
        return self._currency

    def return_url(self) -> str:
        return self._return_url

    def return_url_cancel(self) -> str:
        return self._return_url_cancel

    def push_url(self) -> str:
        return self._push_url

    def platform_name(self) -> str:
        return self._platform_name

    def platform_version(self) -> str:
        return self._platform_version

    def module_supplier(self) -> str:
        return self._module_supplier

    def module_name(self) -> str:
        return self._module_name

    def module_version(self) -> str:
        return self._module_version

    def culture(self) -> str:
        return self._culture

    def channel(self) -> str:
        return self._channel

    def set_mode(self, mode: Optional[str]) -> None:
        if mode:
            self._mode = mode

    def set_logger(self, logger: SubjectInterface) -> None:
        self._logger = logger

    def get_logger(self) -> SubjectInterface:
        if not self._logger:
            raise ValueError("Logger has not been set.")
        return self._logger
