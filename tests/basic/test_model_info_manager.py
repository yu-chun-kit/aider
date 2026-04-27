import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from aider.models import ModelInfoManager


class TestModelInfoManager(TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()
        self.manager = ModelInfoManager()
        # Create a temporary directory for cache
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager.cache_dir = Path(self.temp_dir.name)
        self.manager.cache_file = self.manager.cache_dir / "model_prices_and_context_window.json"
        self.manager.cache_dir.mkdir(exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch("requests.get")
    def test_update_cache_respects_verify_ssl(self, mock_get):
        # OFFLINE FORK: _update_cache should never make network requests
        # Test with default verify_ssl=True
        self.manager._update_cache()
        mock_get.assert_not_called()

        # Test with verify_ssl=False
        self.manager.set_verify_ssl(False)
        self.manager._update_cache()
        mock_get.assert_not_called()

    def test_lazy_loading_cache(self):
        # Create a cache file
        self.manager.cache_file.write_text('{"test_model": {"max_tokens": 4096}}')

        # Verify cache is not loaded on initialization
        self.assertFalse(self.manager._cache_loaded)
        self.assertIsNone(self.manager.content)

        # Access content through get_model_from_cached_json_db
        with patch.object(self.manager, "_update_cache") as mock_update:
            result = self.manager.get_model_from_cached_json_db("test_model")

            # Verify cache was loaded
            self.assertTrue(self.manager._cache_loaded)
            self.assertIsNotNone(self.manager.content)
            self.assertEqual(result, {"max_tokens": 4096})

            # Verify _update_cache was not called since cache exists and is valid
            mock_update.assert_not_called()

    @patch("requests.get")
    def test_verify_ssl_setting_before_cache_loading(self, mock_get):
        # OFFLINE FORK: network requests are disabled
        # Set verify_ssl to False before any cache operations
        self.manager.set_verify_ssl(False)

        # Force cache update by making it look expired
        with patch("time.time", return_value=9999999999):
            # This should trigger _update_cache but not make a network call
            self.manager.get_model_from_cached_json_db("test_model")

            # Verify no network request was made
            mock_get.assert_not_called()
