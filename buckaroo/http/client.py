"""
HTTP Client Module for Buckaroo SDK.

This module provides HTTP client functionality for communicating with the Buckaroo API,
including request/response handling, authentication, and error management.
"""

import json
import time
import hashlib
import hmac
import base64
from typing import Dict, Any, Optional
from urllib.parse import urlencode, quote
import uuid

from ..config.buckaroo_config import BuckarooConfig
from ..exceptions._authentication_error import AuthenticationError
from .strategies import HttpStrategyFactory, HttpResponse


class BuckarooHttpClient:
    """
    HTTP client for Buckaroo API communication.
    
    This class handles all HTTP communication with the Buckaroo API, including:
    - HMAC authentication
    - Request/response handling
    - Retry logic
    - Error handling
    
    Uses a strategy pattern to support different HTTP implementations
    (requests library, curl command, etc.).
    """
    
    def __init__(
        self, 
        store_key: str, 
        secret_key: str, 
        config: BuckarooConfig,
        http_strategy: Optional[str] = None
    ):
        self.store_key = store_key
        self.secret_key = secret_key
        self.config = config
        
        # Create HTTP strategy
        self.http_strategy = HttpStrategyFactory.create_strategy(http_strategy)
        self._configure_strategy()
    
    def _configure_strategy(self) -> None:
        """Configure the HTTP strategy with Buckaroo-specific settings."""
        strategy_config = {
            'timeout': self.config.timeout,
            'verify_ssl': self.config.verify_ssl,
            'retry_attempts': self.config.retry_attempts,
            'retry_delay': self.config.retry_delay,
            'default_headers': self.config.get_request_headers()
        }
        
        self.http_strategy.configure(**strategy_config)
    
    def _generate_hmac_signature(
        self, 
        method: str, 
        url: str, 
        content: str = "", 
        timestamp: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate HMAC authentication headers for Buckaroo API.
        """
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        nonce = str(uuid.uuid4())
    
        # Process content following C# implementation pattern
        if content:
            # Convert content to bytes and compute MD5 hash
            content_bytes = content.encode('utf-8')
            md5_hash = hashlib.md5(content_bytes).digest()
            content_b64 = base64.b64encode(md5_hash).decode('utf-8')
        else:
            content_b64 = ''
        
        # Remove protocol from URL and encode for HMAC signature
        url_without_protocol = url
        if url.startswith('https://'):
            url_without_protocol = url[8:]
        elif url.startswith('http://'):
            url_without_protocol = url[7:]
        
        # URL encode and convert to lowercase (matching C# behavior)
        encoded_url = quote(url_without_protocol, safe='').lower()

        # Create HMAC signature string
        string_to_sign = f"{self.store_key}{method}{encoded_url}{timestamp}{nonce}{content_b64}"

        # Generate HMAC-SHA256 signature
        secret_key_bytes = self.secret_key.encode('utf-8')
        signature_data_bytes = string_to_sign.encode('utf-8')
        signature = hmac.new(secret_key_bytes, signature_data_bytes, hashlib.sha256).digest()
        encoded_signature = base64.b64encode(signature).decode('utf-8')

        return {
            "Authorization": f"hmac {self.store_key}:{encoded_signature}:{nonce}:{timestamp}",
            "X-Buckaroo-Timestamp": timestamp,
            "X-Buckaroo-Store-Key": self.store_key
        }
    
    def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> 'BuckarooResponse':
        """Send a POST request to the Buckaroo API."""
        return self._make_request("POST", endpoint, data, params)
    
    def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> 'BuckarooResponse':
        """Send a GET request to the Buckaroo API."""
        return self._make_request("GET", endpoint, None, params)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> 'BuckarooResponse':
        """Make an HTTP request to the Buckaroo API."""
        # Build full URL
        base_url = self.config.api_endpoint
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        url = f"{base_url}{endpoint}"
        
        # Add URL parameters
        if params:
            url += '?' + urlencode(params)
        
        # Prepare request body
        content = ""
        if data:
            content = json.dumps(data, separators=(',', ':'))
        
        # Generate authentication headers
        auth_headers = self._generate_hmac_signature(method, url, content)
        
        try:
            # Make the request using strategy
            http_response = self.http_strategy.request(
                method=method,
                url=url,
                headers=auth_headers,
                data=content if content else None,
                timeout=self.config.timeout,
                verify_ssl=self.config.verify_ssl
            )
            
            # Create Buckaroo response object
            buckaroo_response = BuckarooResponse(http_response)
            
            # Handle authentication errors
            if http_response.status_code == 401:
                raise AuthenticationError("Authentication failed - check your store key and secret key")
            elif http_response.status_code == 403:
                raise AuthenticationError("Access forbidden - check your API permissions")
            
            return buckaroo_response
            
        except Exception as e:
            # Convert strategy exceptions to BuckarooApiError
            if "timeout" in str(e).lower():
                raise BuckarooApiError(str(e))
            elif "connection" in str(e).lower():
                raise BuckarooApiError(str(e))
            else:
                raise BuckarooApiError(f"Request failed: {str(e)}")


class BuckarooResponse:
    """Wrapper for Buckaroo API responses."""
    
    def __init__(self, response: HttpResponse):
        self._response = response
        self._data = None
        self._parse_response()
    
    def _parse_response(self):
        """Parse the response content."""
        try:
            if self._response.text:
                self._data = json.loads(self._response.text)
            else:
                self._data = {}
        except json.JSONDecodeError:
            self._data = {"raw_content": self._response.text}
    
    @property
    def status_code(self) -> int:
        """Get the HTTP status code."""
        return self._response.status_code
    
    @property
    def success(self) -> bool:
        """Check if the request was successful."""
        return 200 <= self.status_code < 300
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the response data."""
        return self._data or {}
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get the response headers."""
        return self._response.headers
    
    @property
    def text(self) -> str:
        """Get the raw response text."""
        return self._response.text
    
    def json(self) -> Dict[str, Any]:
        """Get the response as JSON."""
        return self.data
    
    def is_successful_payment(self) -> bool:
        """Check if the payment was successful based on Buckaroo response."""
        if not self.success:
            return False
        
        # Check Buckaroo-specific success indicators
        if "Status" in self.data:
            # Buckaroo status codes for successful payments
            success_statuses = [190, 490, 491, 492, 790, 791, 792, 793]
            return self.data.get("Status", {}).get("Code", {}) in success_statuses
        
        return self.success
    
    def get_payment_key(self) -> Optional[str]:
        """Get the payment key from the response."""
        return self.data.get("Key")
    
    def get_transaction_key(self) -> Optional[str]:
        """Get the transaction key from the response."""
        services = self.data.get("Services", [])
        if isinstance(services, list) and services:
            return services[0].get("TransactionKey")
        elif isinstance(services, dict):
            service_list = services.get("ServiceList", [])
            if service_list:
                return service_list[0].get("TransactionKey")
        return None
    
    def get_status_code(self) -> Optional[int]:
        """Get the Buckaroo status code."""
        return self.data.get("Status", {}).get("Code", {})
    
    def get_status_message(self) -> Optional[str]:
        """Get the Buckaroo status message."""
        return self.data.get("Status", {}).get("SubCode", {}).get("Description", "")
    
    def get_redirect_url(self) -> Optional[str]:
        """Get the redirect URL for payments that require redirection."""
        required_action = self.data.get("RequiredAction")
        if required_action and "RedirectURL" in required_action:
            return required_action["RedirectURL"]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "status_code": self.status_code,
            "success": self.success,
            "data": self.data,
            "headers": self.headers,
            "is_successful_payment": self.is_successful_payment(),
            "payment_key": self.get_payment_key(),
            "transaction_key": self.get_transaction_key(),
            "buckaroo_status_code": self.get_status_code(),
            "buckaroo_status_message": self.get_status_message(),
            "redirect_url": self.get_redirect_url()
        }


class BuckarooApiError(Exception):
    """Exception raised for Buckaroo API errors."""
    
    def __init__(self, message: str, response: Optional[BuckarooResponse] = None):
        super().__init__(message)
        self.response = response
    
    @property
    def status_code(self) -> Optional[int]:
        """Get the HTTP status code if available."""
        return self.response.status_code if self.response else None
    
    @property
    def error_data(self) -> Dict[str, Any]:
        """Get the error data if available."""
        return self.response.data if self.response else {}
