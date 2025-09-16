import pytest
import os
import responses

from buckaroo.api.client import Client

@pytest.fixture
def client():
    """Fixture for creating a Buckaroo client."""

    client = Client()

    return client

class ImprovedRequestsMock(responses.RequestsMock):
    """Wrapper adding a few shorthands to responses.RequestMock."""

    def get(self, url, filename, status=200, **kwargs):
        """Setup a mock response for a GET request."""
        body = self._get_body(filename)
        return self.add(responses.GET, url, body=body, status=status, content_type="application/hal+json", **kwargs)

    def post(self, url, filename, status=200, **kwargs):
        """Setup a mock response for a POST request."""
        body = self._get_body(filename)
        return self.add(responses.POST, url, body=body, status=status, content_type="application/hal+json", **kwargs)

    def delete(self, url, filename, status=204, **kwargs):
        """Setup a mock response for a DELETE request."""
        body = self._get_body(filename)
        return self.add(responses.DELETE, url, body=body, status=status, content_type="application/hal+json", **kwargs)

    def patch(self, url, filename, status=200, **kwargs):
        """Setup a mock response for a PATCH request."""
        body = self._get_body(filename)
        return self.add(responses.PATCH, url, body=body, status=status, content_type="application/hal+json", **kwargs)

    def _get_body(self, filename):
        """
        Read the response fixture file and return its contents as a string.

        Args:
            filename (str): The name of the fixture file (without extension).

        Returns:
            str: The contents of the fixture file.

        Raises:
            FileNotFoundError: If the fixture file does not exist.
            IOError: If there is an error reading the file.
        """
        file = os.path.join(os.path.dirname(__file__), "responses", f"{filename}.json")
        try:
            with open(file, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Fixture file not found: {file}") from e
        except IOError as e:
            raise IOError(f"Error reading fixture file: {file}") from e

@pytest.fixture
def response():
    """Set up the responses fixture."""
    with ImprovedRequestsMock() as mock:
        yield mock