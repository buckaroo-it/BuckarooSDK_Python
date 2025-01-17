class Response:
    def __init__(self, http_response: dict, data: dict):
        self.http_response = http_response
        self.data = data

    def __getattr__(self, name):
        if name.startswith("get"):
            param = name[3:]
            if param in self.data:
                return self.data[param]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def get_http_response(self) -> dict:
        return self.http_response

    def to_dict(self) -> dict:
        return self.data
