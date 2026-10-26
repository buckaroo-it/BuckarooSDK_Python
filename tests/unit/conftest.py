"""Shared fixtures for unit tests."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from buckaroo._buckaroo_client import BuckarooClient
from tests.support.mock_buckaroo import MockBuckaroo


@pytest.fixture
def client(mock_strategy: MockBuckaroo) -> BuckarooClient:
    """BuckarooClient wired to ``mock_strategy`` — no real HTTP."""
    c = BuckarooClient("store_key", "secret_key", mode="test")
    c.http_client.http_strategy = mock_strategy
    return c


_BUCKAROO_ENV_VARS = (
    "BUCKAROO_STORE_KEY",
    "BUCKAROO_SECRET_KEY",
    "BUCKAROO_MODE",
    "BUCKAROO_LOG_LEVEL",
    "BUCKAROO_LOG_DESTINATION",
    "BUCKAROO_LOG_FILE",
    "BUCKAROO_LOG_MASK_SENSITIVE",
    "BUCKAROO_TIMEOUT",
    "BUCKAROO_RETRY_ATTEMPTS",
)


@pytest.fixture(autouse=True)
def _clean_buckaroo_env(monkeypatch):
    """Start every test with a clean BUCKAROO_* environment."""
    for name in _BUCKAROO_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def env_credentials(monkeypatch):
    """Set default BUCKAROO_STORE_KEY / BUCKAROO_SECRET_KEY and return monkeypatch for chaining."""
    monkeypatch.setenv("BUCKAROO_STORE_KEY", "sk")
    monkeypatch.setenv("BUCKAROO_SECRET_KEY", "ss")
    return monkeypatch


@pytest.fixture
def local_endpoint():
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            received.append((self.command, dict(self.headers), body))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"access_token":"synthetic-token"}')

        do_PUT = do_POST
        do_PATCH = do_POST
        do_GET = do_POST

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/token", received
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
