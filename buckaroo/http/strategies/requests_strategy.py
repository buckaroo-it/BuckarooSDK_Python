"""
Requests-based HTTP Strategy for Buckaroo SDK.

This module provides an HTTP strategy implementation using the requests library.
"""

from typing import Dict, Optional
from .http_strategy import HttpStrategy, HttpResponse

try:
    import requests
    from requests.adapters import HTTPAdapter

    try:
        from urllib3.util.retry import Retry
    except ImportError:
        from requests.packages.urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

    # Create dummy classes for type hints when requests is not available
    class HTTPAdapter:
        pass

    class Retry:
        pass


class RequestsStrategy(HttpStrategy):
    """
    HTTP strategy implementation using the requests library.

    This strategy provides robust HTTP functionality with retry logic,
    session management, and connection pooling.
    """

    def __init__(self):
        super().__init__()
        self.session = None
        self._retry_attempts = 3
        self._retry_delay = 1.0

    def configure(self, **kwargs) -> None:
        """
        Configure the requests session with retry logic and adapters.

        Args:
            **kwargs: Configuration parameters
                - retry_attempts: Number of retry attempts
                - retry_delay: Delay between retries
                - default_headers: Default headers to set
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "The 'requests' library is required for RequestsStrategy. "
                "Please install it with: pip install requests"
            )

        self._retry_attempts = kwargs.get("retry_attempts", 3)
        self._retry_delay = kwargs.get("retry_delay", 1.0)

        # Create session
        self.session = requests.Session()

        # Configure retry strategy if available
        try:
            retry_strategy = Retry(
                total=self._retry_attempts,
                backoff_factor=self._retry_delay,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST", "GET", "PUT", "DELETE"],
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        except (NameError, TypeError):
            # Fallback if Retry is not available
            adapter = HTTPAdapter(max_retries=self._retry_attempts)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

        # Set default headers
        default_headers = kwargs.get("default_headers", {})
        if default_headers:
            self.session.headers.update(default_headers)

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
        Make an HTTP request using requests library.

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
        if not self.session:
            self.configure()

        request_kwargs = {
            "method": method,
            "url": url,
            "headers": headers or {},
            "timeout": timeout or 30,
            "verify": verify_ssl,
        }

        if data:
            request_kwargs["data"] = data

        try:
            response = self.session.request(**request_kwargs)

            return HttpResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                text=response.text,
                success=200 <= response.status_code < 300,
            )

        except requests.exceptions.Timeout:
            if timeout is not None:
                raise Exception(f"Request timeout after {timeout} seconds")
            raise Exception("Request timeout")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check your internet connection")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def is_available(self) -> bool:
        """
        Check if requests library is available.

        Returns:
            bool: True if requests is available
        """
        return REQUESTS_AVAILABLE

    def get_name(self) -> str:
        """
        Get the name of this strategy.

        Returns:
            str: Strategy name
        """
        return "requests"
