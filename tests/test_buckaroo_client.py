import unittest
from buckaroo._buckaroo_client import BuckarooClient
from buckaroo.exceptions._authentication_error import AuthenticationError


class TestBuckarooClient(unittest.TestCase):
    """Test suite for BuckarooClient class."""

    def test_init_with_valid_parameters(self):
        """Test that BuckarooClient initializes correctly with valid parameters."""
        store_key = "test_store_key"
        secret_key = "test_secret_key"
        
        client = BuckarooClient(store_key, secret_key)
        
        # Verify the client was created successfully and stores the keys
        self.assertIsInstance(client, BuckarooClient)
        self.assertEqual(client.store_key, "test_store_key")
        self.assertEqual(client.secret_key, "test_secret_key")

    def test_init_strips_whitespace_from_keys(self):
        """Test that whitespace is stripped from store_key and secret_key."""
        store_key = "  test_store_key  "
        secret_key = "  test_secret_key  "
        
        client = BuckarooClient(store_key, secret_key)
        
        self.assertEqual(client.store_key, "test_store_key")
        self.assertEqual(client.secret_key, "test_secret_key")

    def test_init_raises_error_when_store_key_is_none(self):
        """Test that AuthenticationError is raised when store_key is None."""
        secret_key = "test_secret_key"
        
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient(None, secret_key)
        
        self.assertEqual(str(context.exception), "Store key must be provided")

    def test_init_raises_error_when_store_key_is_empty_string(self):
        """Test that AuthenticationError is raised when store_key is an empty string."""
        secret_key = "test_secret_key"
        
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient("", secret_key)
        
        self.assertEqual(str(context.exception), "Store key must be provided")

    def test_init_raises_error_when_store_key_is_whitespace_only(self):
        """Test that AuthenticationError is raised when store_key contains only whitespace."""
        secret_key = "test_secret_key"
        
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient("   ", secret_key)
        
        self.assertEqual(str(context.exception), "Store key must be provided")

    def test_init_raises_error_when_secret_key_is_none(self):
        """Test that AuthenticationError is raised when secret_key is None."""
        store_key = "test_store_key"
        
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient(store_key, None)
        
        self.assertEqual(str(context.exception), "Secret key must be provided")

    def test_init_raises_error_when_secret_key_is_empty_string(self):
        """Test that AuthenticationError is raised when secret_key is an empty string."""
        store_key = "test_store_key"
        
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient(store_key, "")
        
        self.assertEqual(str(context.exception), "Secret key must be provided")

    def test_init_raises_error_when_secret_key_is_whitespace_only(self):
        """Test that AuthenticationError is raised when secret_key contains only whitespace."""
        store_key = "test_store_key"
        
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient(store_key, "   ")
        
        self.assertEqual(str(context.exception), "Secret key must be provided")

    def test_init_raises_error_when_both_keys_are_none(self):
        """Test that AuthenticationError is raised when both keys are None."""
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient(None, None)
        
        # Should raise for store_key first since it's checked first
        self.assertEqual(str(context.exception), "Store key must be provided")

    def test_init_with_various_valid_inputs(self):
        """Test initialization with various valid input combinations."""
        test_cases = [
            ("valid_store", "valid_secret"),
            ("store123", "secret456"),
            ("store-key", "secret_key"),
            ("store.key", "secret.key"),
            ("STORE_KEY", "SECRET_KEY"),
            ("store_key_with_underscores", "secret_key_with_underscores"),
        ]
        
        for store_key, secret_key in test_cases:
            with self.subTest(store_key=store_key, secret_key=secret_key):
                client = BuckarooClient(store_key, secret_key)
                self.assertIsInstance(client, BuckarooClient)
                self.assertEqual(client.store_key, store_key)
                self.assertEqual(client.secret_key, secret_key)


class TestBuckarooClientErrorHandling(unittest.TestCase):
    """Test suite for BuckarooClient error handling."""

    def test_authentication_error_is_subclass_of_expected_exception(self):
        """Test that AuthenticationError is properly structured."""
        try:
            BuckarooClient(None, "secret")
        except Exception as e:
            self.assertIsInstance(e, AuthenticationError)

    def test_error_messages_are_descriptive(self):
        """Test that error messages are clear and helpful."""
        # Test store key error message
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient(None, "secret")
        self.assertIn("Store key", str(context.exception))
        
        # Test secret key error message  
        with self.assertRaises(AuthenticationError) as context:
            BuckarooClient("store", None)
        self.assertIn("Secret key", str(context.exception))


if __name__ == '__main__':
    unittest.main()