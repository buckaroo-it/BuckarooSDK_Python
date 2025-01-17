from abc import ABC, abstractmethod
from typing import Any, Mapping


class HttpClientInterface(ABC):

    @abstractmethod
    def call(
        self, url: str, headers: dict, method: str, data: Mapping[str, Any] | None
    ) -> Any:
        pass
