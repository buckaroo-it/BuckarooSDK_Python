import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from buckaroo.http.client import BuckarooHttpClient, BuckarooResponse, BuckarooApiError
from buckaroo.config.buckaroo_config import BuckarooConfig, Environment
from buckaroo.exceptions._authentication_error import AuthenticationError


class MockResponse:
    """Mock response object for testing."""
    
    def __init__(self, json_data, status_code=200, headers=None, text=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text or json.dumps(json_data) if json_data else ""
        self._json_data = json_data
    
    def json(self):
        return self._json_data if self._json_data else {}


class TestBuckarooHttpClient(unittest.TestCase):
    """Test suite for BuckarooHttpClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = BuckarooConfig(
            environment=Environment.TEST,
            timeout=30,
            retry_attempts=3
        )
        self.store_key = "test_store_key"
        self.secret_key = "test_secret_key"

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_http_client_creation(self, mock_requests):
        """Test HTTP client creation."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        client = BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        self.assertEqual(client.store_key, self.store_key)
        self.assertEqual(client.secret_key, self.secret_key)
        self.assertEqual(client.config, self.config)
        self.assertIsNotNone(client.session)

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', False)
    def test_http_client_missing_requests(self):
        """Test HTTP client creation when requests is not available."""
        with self.assertRaises(ImportError) as context:
            BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        self.assertIn("The 'requests' library is required", str(context.exception))

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_hmac_signature_generation(self, mock_requests):
        """Test HMAC signature generation."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        client = BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        method = "POST"
        url = "https://testcheckout.buckaroo.nl/json/Transaction"
        content = '{"test":"data"}'
        timestamp = "1234567890"
        
        headers = client._generate_hmac_signature(method, url, content, timestamp)
        
        self.assertIn("Authorization", headers)
        self.assertIn("X-Buckaroo-Timestamp", headers)
        self.assertIn("X-Buckaroo-Store-Key", headers)
        self.assertEqual(headers["X-Buckaroo-Timestamp"], timestamp)
        self.assertEqual(headers["X-Buckaroo-Store-Key"], self.store_key)
        self.assertTrue(headers["Authorization"].startswith("hmac"))

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_post_request(self, mock_requests):
        """Test POST request."""
        mock_response = MockResponse({"status": "success"}, 200)
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        client = BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        data = {"test": "data"}
        response = client.post("/json/Transaction", data)
        
        self.assertIsInstance(response, BuckarooResponse)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.success)
        mock_session.request.assert_called_once()

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_get_request(self, mock_requests):
        """Test GET request."""
        mock_response = MockResponse({"data": "test"}, 200)
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        client = BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        params = {"param1": "value1"}
        response = client.get("/json/Status", params)
        
        self.assertIsInstance(response, BuckarooResponse)
        self.assertEqual(response.status_code, 200)
        mock_session.request.assert_called_once()

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_authentication_error_401(self, mock_requests):
        """Test authentication error on 401 response."""
        mock_response = MockResponse({"error": "unauthorized"}, 401)
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        client = BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        with self.assertRaises(AuthenticationError):
            client.post("/json/Transaction", {"test": "data"})

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_authentication_error_403(self, mock_requests):
        """Test authentication error on 403 response."""
        mock_response = MockResponse({"error": "forbidden"}, 403)
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        client = BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        with self.assertRaises(AuthenticationError):
            client.post("/json/Transaction", {"test": "data"})

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_timeout_error(self, mock_requests):
        """Test timeout error handling."""
        mock_session = Mock()
        mock_session.request.side_effect = mock_requests.exceptions.Timeout("Timeout")
        mock_requests.Session.return_value = mock_session
        mock_requests.exceptions = Mock()
        mock_requests.exceptions.Timeout = Exception
        mock_requests.exceptions.ConnectionError = ConnectionError
        mock_requests.exceptions.RequestException = Exception
        
        client = BuckarooHttpClient(self.store_key, self.secret_key, self.config)
        
        with self.assertRaises(BuckarooApiError) as context:
            client.post("/json/Transaction", {"test": "data"})
        
        self.assertIn("timeout", str(context.exception).lower())


class TestBuckarooResponse(unittest.TestCase):
    """Test suite for BuckarooResponse."""

    def test_successful_response(self):
        """Test successful response handling."""
        mock_response = MockResponse({"status": "success"}, 200)
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.success)
        self.assertEqual(response.data, {"status": "success"})

    def test_error_response(self):
        """Test error response handling."""
        mock_response = MockResponse({"error": "bad request"}, 400)
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.success)
        self.assertEqual(response.data, {"error": "bad request"})

    def test_empty_response(self):
        """Test empty response handling."""
        mock_response = MockResponse(None, 204, text="")
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.status_code, 204)
        self.assertTrue(response.success)
        self.assertEqual(response.data, {})

    def test_invalid_json_response(self):
        """Test invalid JSON response handling."""
        mock_response = MockResponse(None, 200, text="invalid json")
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.success)
        self.assertIn("raw_content", response.data)
        self.assertEqual(response.data["raw_content"], "invalid json")

    def test_successful_payment_status(self):
        """Test successful payment status detection."""
        # Test successful status code
        mock_response = MockResponse({
            "Status": {"Code": 190},
            "Key": "payment123"
        }, 200)
        response = BuckarooResponse(mock_response)
        
        self.assertTrue(response.is_successful_payment())
        self.assertEqual(response.get_payment_key(), "payment123")

    def test_failed_payment_status(self):
        """Test failed payment status detection."""
        mock_response = MockResponse({
            "Status": {"Code": 690},  # Failed status
            "Key": "payment123"
        }, 200)
        response = BuckarooResponse(mock_response)
        
        self.assertFalse(response.is_successful_payment())

    def test_payment_key_extraction(self):
        """Test payment key extraction."""
        mock_response = MockResponse({"Key": "ABC123"}, 200)
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.get_payment_key(), "ABC123")

    def test_transaction_key_extraction(self):
        """Test transaction key extraction."""
        mock_response = MockResponse({
            "Services": {
                "ServiceList": [
                    {"TransactionKey": "TXN123"}
                ]
            }
        }, 200)
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.get_transaction_key(), "TXN123")

    def test_status_message_extraction(self):
        """Test status message extraction."""
        mock_response = MockResponse({
            "Status": {
                "Code": 190,
                "SubCode": {
                    "Description": "Payment successful"
                }
            }
        }, 200)
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.get_status_code(), 190)
        self.assertEqual(response.get_status_message(), "Payment successful")

    def test_redirect_url_extraction(self):
        """Test redirect URL extraction."""
        mock_response = MockResponse({
            "RequiredAction": {
                "RedirectURL": "https://example.com/redirect"
            }
        }, 200)
        response = BuckarooResponse(mock_response)
        
        self.assertEqual(response.get_redirect_url(), "https://example.com/redirect")

    def test_to_dict_conversion(self):
        """Test response to dictionary conversion."""
        mock_response = MockResponse({
            "Status": {"Code": 190},
            "Key": "payment123"
        }, 200)
        response = BuckarooResponse(mock_response)
        
        response_dict = response.to_dict()
        
        self.assertEqual(response_dict["status_code"], 200)
        self.assertTrue(response_dict["success"])
        self.assertEqual(response_dict["payment_key"], "payment123")
        self.assertEqual(response_dict["buckaroo_status_code"], 190)
        self.assertTrue(response_dict["is_successful_payment"])


class TestBuckarooApiError(unittest.TestCase):
    """Test suite for BuckarooApiError."""

    def test_api_error_creation(self):
        """Test API error creation."""
        error = BuckarooApiError("Test error message")
        
        self.assertEqual(str(error), "Test error message")
        self.assertIsNone(error.response)
        self.assertIsNone(error.status_code)

    def test_api_error_with_response(self):
        """Test API error with response."""
        mock_response = MockResponse({"error": "server error"}, 500)
        response = BuckarooResponse(mock_response)
        error = BuckarooApiError("Server error", response)
        
        self.assertEqual(str(error), "Server error")
        self.assertEqual(error.response, response)
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.error_data, {"error": "server error"})


class TestHttpClientIntegration(unittest.TestCase):
    """Integration tests for HTTP client with payment builders."""

    @patch('buckaroo.http.client.REQUESTS_AVAILABLE', True)
    @patch('buckaroo.http.client.requests')
    def test_payment_execution_integration(self, mock_requests):
        """Test payment execution through HTTP client."""
        # Mock successful payment response
        payment_response = {
            "Status": {"Code": 190},
            "Key": "payment123",
            "Services": {
                "ServiceList": [
                    {"TransactionKey": "TXN123"}
                ]
            }
        }
        
        mock_response = MockResponse(payment_response, 200)
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        # Create client and payment
        from buckaroo._buckaroo_client import BuckarooClient
        client = BuckarooClient(
            "test_store_key", 
            "test_secret_key", 
            config=self.config if hasattr(self, 'config') else BuckarooConfig()
        )
        
        # This would normally require a proper payment builder setup
        # For now, just test that the HTTP client is available
        self.assertIsNotNone(client.http_client)
        self.assertIsInstance(client.http_client, BuckarooHttpClient)


if __name__ == '__main__':
    unittest.main()