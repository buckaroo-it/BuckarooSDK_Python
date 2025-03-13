import src.transaction.http_client.curl_client as curl_client
import src.transaction.http_client.default_http_client as default_http_client
import src.transaction.http_client.http_client_interface as http_client_interface


# @TODO: We have two different clients, on what condition should CurlClient be returned?
def create_client() -> http_client_interface.HttpClientInterface:
    return default_http_client.DefaultHttpClient()
