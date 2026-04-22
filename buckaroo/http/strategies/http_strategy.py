"""
HTTP Strategy Interface for Buckaroo SDK.

This module defines the abstract base class for HTTP client strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class HttpResponse:
    """
    Response object returned by HTTP strategies.

    This provides a consistent interface across different HTTP implementations.
    """

    status_code: int
    headers: Dict[str, str]
    text: str
    success: bool

    def json(self) -> Dict[str, Any]:
        """Parse response text as JSON."""
        import json

        try:
            return json.loads(self.text) if self.text else {}
        except json.JSONDecodeError:
            return {"raw_content": self.text}


class HttpStrategy(ABC):
    """
    Abstract base class for HTTP client strategies.

    This defines the interface that all HTTP client implementations must follow.
    """

    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        Configure the HTTP client with settings like timeout, retry, etc.

        Args:
            **kwargs: Configuration parameters specific to the implementation
        """

    @abstractmethod
    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: bool = True,
    ) -> HttpResponse:
        """
        Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            data: Request body data
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates

        Returns:
            HttpResponse: Response object

        Raises:
            Exception: If the request fails
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this HTTP strategy is available on the system.

        Returns:
            bool: True if the strategy can be used
        """

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of this HTTP strategy.

        Returns:
            str: Strategy name
        """
