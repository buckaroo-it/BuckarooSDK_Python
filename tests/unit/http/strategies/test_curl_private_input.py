"""Real curl requests preserve payloads without exposing them in argv."""

import base64
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from buckaroo.http.strategies import CurlStrategy
from buckaroo.services.hosted_fields_service import HostedFieldsService


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


@pytest.mark.skipif(not shutil.which("curl"), reason="curl is required")
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
def test_private_headers_and_body_reach_server_unchanged(local_endpoint, monkeypatch, method):
    url, received = local_endpoint
    strategy = CurlStrategy()
    strategy.configure(default_headers={"X-Default": "synthetic-default", "X-Shared": "default"})
    body = '@not-a-file\n"\nurl = "http://127.0.0.1:1/injected"\n# café\t\\end\r\n'
    authorization = "hmac synthetic:signature:nonce:timestamp"
    header_value = 'synthetic-"quoted"-\\value'
    real_run = subprocess.run

    def inspect_command(cmd, **kwargs):
        for secret in (body, authorization, header_value, "synthetic-default"):
            assert secret not in " ".join(cmd)
        assert kwargs.get("shell", False) is False
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", inspect_command)
    response = strategy.request(
        method,
        url,
        headers={"Authorization": authorization, "X-Test": header_value, "X-Shared": "per-call"},
        data=body,
        timeout=5,
    )
    assert response.status_code == 200
    assert len(received) == 1
    actual_method, headers, actual_body = received[0]
    assert actual_method == method
    assert actual_body == body.encode("utf-8")
    assert headers["Authorization"] == authorization
    assert headers["X-Test"] == header_value
    assert headers["X-Default"] == "synthetic-default"
    assert headers["X-Shared"] == "per-call"


@pytest.mark.skipif(not shutil.which("curl"), reason="curl is required")
def test_hosted_fields_basic_credentials_are_private(local_endpoint, monkeypatch):
    url, received = local_endpoint
    service = HostedFieldsService("synthetic-id", "synthetic-secret", http_strategy=CurlStrategy())
    monkeypatch.setattr(service, "OAUTH_TOKEN_URL", url)
    authorization = "Basic " + base64.b64encode(b"synthetic-id:synthetic-secret").decode()
    real_run = subprocess.run

    def inspect_command(cmd, **kwargs):
        assert authorization not in " ".join(cmd)
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", inspect_command)
    assert service.get_token() == {"access_token": "synthetic-token"}
    assert received[0][1]["Authorization"] == authorization
    assert received[0][2] == b"scope=hostedfields%3Asave&grant_type=client_credentials"
