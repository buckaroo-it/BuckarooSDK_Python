from .curl_client import CurlClient
from .default_http_client import DefaultHttpClient
from .http_client_interface import HttpClientInterface


# @TODO: We have two different clients, on what condition should CurlClient be returned?
def create_client() -> HttpClientInterface:
    return DefaultHttpClient()
