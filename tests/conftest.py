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
        """Read the response fixture file and return it."""
        file = os.path.join(os.path.dirname(__file__), "responses", f"{filename}.json")
        with open(file, encoding="utf-8") as f:
            return f.read()

@pytest.fixture
def response():
    """Set up the responses fixture."""
    with ImprovedRequestsMock() as mock:
        yield mock