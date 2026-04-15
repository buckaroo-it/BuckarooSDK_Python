"""
HTTP Strategy Interface for Buckaroo SDK.

This module defines the abstract base class for HTTP client strategies.
"""

import json as _json
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
        try:
            return _json.loads(self.text) if self.text else {}
        except _json.JSONDecodeError:
            return {"raw_content": self.text}


class HttpStrategy(ABC):
    """
    Abstract base class for HTTP client strategies.

    Stores common configuration fields and provides a default :meth:`configure`
    implementation.  Subclasses that need extra setup should call
    ``super().configure(**kwargs)`` before their own logic.
    """

    def __init__(self) -> None:
        self._timeout: int = 30
        self._verify_ssl: bool = True
        self._retry_attempts: int = 3
        self._retry_delay: float = 1.0
        self._default_headers: Dict[str, str] = {}

    def configure(self, **kwargs) -> None:
        """Store common configuration shared by all strategies."""
        self._timeout = kwargs.get('timeout', self._timeout)
        self._verify_ssl = kwargs.get('verify_ssl', self._verify_ssl)
        self._retry_attempts = kwargs.get('retry_attempts', self._retry_attempts)
        self._retry_delay = kwargs.get('retry_delay', self._retry_delay)
        self._default_headers = kwargs.get('default_headers', self._default_headers)

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
        """Make an HTTP request and return an :class:`HttpResponse`."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this strategy can be used on the current system."""

    @abstractmethod
    def get_name(self) -> str:
        """Return a short identifier for this strategy (e.g. ``'requests'``)."""
