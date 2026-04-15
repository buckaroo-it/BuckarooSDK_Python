"""
cURL-based HTTP Strategy for Buckaroo SDK.

This module provides an HTTP strategy implementation using system curl command.
"""

import subprocess
import shutil
from typing import Dict, Any, Optional, List
from .http_strategy import HttpStrategy, HttpResponse


class CurlStrategy(HttpStrategy):
    """
    HTTP strategy implementation using system curl command.
    
    This strategy provides HTTP functionality without external Python dependencies,
    using the curl command available on most systems.
    """
    
    def __init__(self):
        super().__init__()

    def configure(self, **kwargs) -> None:
        super().configure(**kwargs)
    
    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        timeout: Optional[int] = None,
        verify_ssl: bool = True
    ) -> HttpResponse:
        """
        Make an HTTP request using curl command.
        
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
        # Build curl command
        cmd = self._build_curl_command(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=timeout or self._timeout,
            verify_ssl=verify_ssl
        )
        
        # Execute curl with retry logic
        last_exception = None
        for attempt in range(self._retry_attempts):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout or self._timeout,
                    check=False  # Don't raise on non-zero exit codes
                )
                
                return self._parse_curl_output(result)
                
            except subprocess.TimeoutExpired:
                last_exception = Exception(f"Request timeout after {timeout or self._timeout} seconds")
                if attempt == self._retry_attempts - 1:
                    raise last_exception
            except subprocess.SubprocessError as e:
                last_exception = Exception(f"Curl command failed: {str(e)}")
                if attempt == self._retry_attempts - 1:
                    raise last_exception
            except Exception as e:
                last_exception = Exception(f"Request failed: {str(e)}")
                if attempt == self._retry_attempts - 1:
                    raise last_exception
    
    def _build_curl_command(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ) -> List[str]:
        """
        Build the curl command arguments.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            data: Request body data
            timeout: Request timeout
            verify_ssl: Whether to verify SSL
            
        Returns:
            List[str]: Curl command arguments
        """
        cmd = [
            'curl',
            '-X', method.upper(),
            '--location',  # Follow redirects
            '--silent',    # Silent mode
            '--show-error', # Show errors
            '--fail-with-body',  # Include response body on HTTP errors
            '--max-time', str(timeout),
            '--include',   # Include headers in output
        ]
        
        # SSL verification
        if not verify_ssl:
            cmd.extend(['--insecure'])
        
        # Add headers
        all_headers = {**self._default_headers}
        if headers:
            all_headers.update(headers)
        
        for key, value in all_headers.items():
            cmd.extend(['-H', f'{key}: {value}'])
        
        # Add data for POST/PUT requests
        if data and method.upper() in ['POST', 'PUT', 'PATCH']:
            cmd.extend(['--data', data])
        
        # Add URL last
        cmd.append(url)
        
        return cmd
    
    def _parse_curl_output(self, result: subprocess.CompletedProcess) -> HttpResponse:
        """
        Parse curl output into HttpResponse object.
        
        Args:
            result: Completed curl process result
            
        Returns:
            HttpResponse: Parsed response
        """
        output = result.stdout
        
        if not output:
            # Handle empty response
            return HttpResponse(
                status_code=result.returncode,
                headers={},
                text="",
                success=result.returncode == 0
            )
        
        # Split headers and body
        # curl --include puts headers before the body, separated by \r\n\r\n
        if '\r\n\r\n' in output:
            header_section, body = output.split('\r\n\r\n', 1)
        elif '\n\n' in output:
            header_section, body = output.split('\n\n', 1)
        else:
            # No clear separation, treat all as body
            header_section = ""
            body = output
        
        # Parse status code and headers
        status_code = 0
        headers = {}
        
        if header_section:
            lines = header_section.split('\n')
            if lines:
                # First line contains status
                status_line = lines[0].strip()
                if 'HTTP/' in status_line:
                    try:
                        status_code = int(status_line.split()[1])
                    except (IndexError, ValueError):
                        status_code = result.returncode if result.returncode != 0 else 500
                
                # Parse headers
                for line in lines[1:]:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers[key.strip()] = value.strip()
        else:
            # No headers section, use return code
            status_code = result.returncode if result.returncode != 0 else 200
        
        # If curl failed but we have output, it might be an error message
        if result.returncode != 0 and not body.strip():
            body = result.stderr or f"Curl failed with exit code {result.returncode}"
        
        return HttpResponse(
            status_code=status_code,
            headers=headers,
            text=body,
            success=200 <= status_code < 300
        )
    
    def is_available(self) -> bool:
        """
        Check if curl command is available on the system.
        
        Returns:
            bool: True if curl is available
        """
        return shutil.which('curl') is not None
    
    def get_name(self) -> str:
        """
        Get the name of this strategy.
        
        Returns:
            str: Strategy name
        """
        return "curl"