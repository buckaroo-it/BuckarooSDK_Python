import subprocess
import json
from typing import Any

import src.transaction.http_client.http_client_interface as http_client_interface


class CurlClient(http_client_interface.HttpClientInterface):
    def call(self, url: str, headers: dict, method: str, data: str | None) -> Any:
        try:
            command = [
                "curl",
                "-X",
                method.upper(),
                url,
            ]

            for key, value in headers.items():
                command.extend(["-H", f"{key}: {value}"])

            if data:
                json_data = json.dumps(data)
                command.extend(["-d", json_data])

            result = subprocess.run(command, text=True, capture_output=True, check=True)

            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"Curl command failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")
