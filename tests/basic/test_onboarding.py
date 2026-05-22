import argparse
import base64
import hashlib
import os
import unittest
from unittest.mock import MagicMock, patch

# Import the functions to be tested
from aider.onboarding import (
    check_openrouter_tier,
    exchange_code_for_key,
    find_available_port,
    generate_pkce_codes,
    offer_openrouter_oauth,
    select_default_model,
    try_to_select_default_model,
)


# Mock the Analytics class as it's used in some functions
class DummyAnalytics:
    def event(self, *args, **kwargs):
        pass


# Mock the InputOutput class
class DummyIO:
    def tool_output(self, *args, **kwargs):
        pass

    def tool_warning(self, *args, **kwargs):
        pass

    def tool_error(self, *args, **kwargs):
        pass

    def confirm_ask(self, *args, **kwargs):
        return False  # Default to no confirmation

    def offer_url(self, *args, **kwargs):
        pass


class TestOnboarding(unittest.TestCase):
    # OFFLINE FORK: check_openrouter_tier is disabled and always returns True
    def test_check_openrouter_tier_returns_true(self):
        """Test check_openrouter_tier is disabled in offline mode."""
        self.assertTrue(check_openrouter_tier("fake_key"))

    @patch.dict(os.environ, {}, clear=True)
    def test_try_select_default_model_no_keys(self):
        """Test no model is selected when no keys are present."""
        self.assertIsNone(try_to_select_default_model())

    # OFFLINE FORK: OpenRouter is not supported
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "or_key"}, clear=True)
    def test_try_select_default_model_openrouter_not_supported(self):
        """Test OpenRouter is not supported in offline mode."""
        self.assertIsNone(try_to_select_default_model())

    # OFFLINE FORK: Anthropic is not supported
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "an_key"}, clear=True)
    def test_try_select_default_model_anthropic_not_supported(self):
        """Test Anthropic is not supported in offline mode."""
        self.assertIsNone(try_to_select_default_model())

    # OFFLINE FORK: DeepSeek is not supported
    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "ds_key"}, clear=True)
    def test_try_select_default_model_deepseek_not_supported(self):
        """Test Deepseek is not supported in offline mode."""
        self.assertIsNone(try_to_select_default_model())

    # OFFLINE FORK: OpenAI API key maps to local-model
    @patch.dict(os.environ, {"OPENAI_API_KEY": "oa_key"}, clear=True)
    def test_try_select_default_model_openai_without_local_base(self):
        """Test OpenAI-compatible model selection requires a local or intranet API base."""
        self.assertIsNone(try_to_select_default_model())

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "oa_key", "OPENAI_API_BASE": "http://127.0.0.1:1234/v1"},
        clear=True,
    )
    def test_try_select_default_model_openai(self):
        """Test OpenAI-compatible local server model selection."""
        self.assertEqual(try_to_select_default_model(), "openai/local-model")

    # OFFLINE FORK: Gemini is not supported
    @patch.dict(os.environ, {"GEMINI_API_KEY": "gm_key"}, clear=True)
    def test_try_select_default_model_gemini_not_supported(self):
        """Test Gemini is not supported in offline mode."""
        self.assertIsNone(try_to_select_default_model())

    # OFFLINE FORK: Vertex AI is not supported
    @patch.dict(os.environ, {"VERTEXAI_PROJECT": "vx_proj"}, clear=True)
    def test_try_select_default_model_vertex_not_supported(self):
        """Test Vertex AI is not supported in offline mode."""
        self.assertIsNone(try_to_select_default_model())

    # OFFLINE FORK: Ollama is supported
    @patch.dict(os.environ, {"OLLAMA_API_KEY": "ol_key"}, clear=True)
    def test_try_select_default_model_ollama(self):
        """Test Ollama model selection."""
        self.assertEqual(try_to_select_default_model(), "ollama/llama3")

    # OFFLINE FORK: Ollama takes priority over OpenAI
    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "oa_key",
            "OPENAI_API_BASE": "http://127.0.0.1:1234/v1",
            "OLLAMA_API_KEY": "ol_key",
        },
        clear=True,
    )
    def test_try_select_default_model_priority_ollama(self):
        """Test Ollama key takes priority over OpenAI in offline mode."""
        self.assertEqual(try_to_select_default_model(), "ollama/llama3")

    @patch("socketserver.TCPServer")
    def test_find_available_port_success(self, mock_tcp_server):
        """Test finding an available port."""
        # Simulate port 8484 being available
        mock_tcp_server.return_value.__enter__.return_value = None  # Allow context manager
        port = find_available_port(start_port=8484, end_port=8484)
        self.assertEqual(port, 8484)
        mock_tcp_server.assert_called_once_with(("localhost", 8484), None)

    @patch("socketserver.TCPServer")
    def test_find_available_port_in_use(self, mock_tcp_server):
        """Test finding the next available port if the first is in use."""
        # Simulate port 8484 raising OSError, 8485 being available
        mock_tcp_server.side_effect = [OSError, MagicMock()]
        mock_tcp_server.return_value.__enter__.return_value = None  # Allow context manager
        port = find_available_port(start_port=8484, end_port=8485)
        self.assertEqual(port, 8485)
        self.assertEqual(mock_tcp_server.call_count, 2)
        mock_tcp_server.assert_any_call(("localhost", 8484), None)
        mock_tcp_server.assert_any_call(("localhost", 8485), None)

    @patch("socketserver.TCPServer", side_effect=OSError)
    def test_find_available_port_none_available(self, mock_tcp_server):
        """Test returning None if no ports are available in the range."""
        port = find_available_port(start_port=8484, end_port=8485)
        self.assertIsNone(port)
        self.assertEqual(mock_tcp_server.call_count, 2)  # Tried 8484 and 8485

    def test_generate_pkce_codes(self):
        """Test PKCE code generation."""
        verifier, challenge = generate_pkce_codes()
        self.assertIsInstance(verifier, str)
        self.assertIsInstance(challenge, str)
        self.assertGreater(len(verifier), 40)  # Check reasonable length
        self.assertGreater(len(challenge), 40)
        # Verify the challenge is the SHA256 hash of the verifier, base64 encoded
        hasher = hashlib.sha256()
        hasher.update(verifier.encode("utf-8"))
        expected_challenge = base64.urlsafe_b64encode(hasher.digest()).rstrip(b"=").decode("utf-8")
        self.assertEqual(challenge, expected_challenge)

    # OFFLINE FORK: exchange_code_for_key is disabled
    def test_exchange_code_for_key_disabled(self):
        """Test exchange_code_for_key is disabled in offline mode."""
        io_mock = DummyIO()
        io_mock.tool_error = MagicMock()

        api_key = exchange_code_for_key("auth_code", "verifier", io_mock)

        self.assertIsNone(api_key)
        io_mock.tool_error.assert_called_once_with("OpenRouter OAuth is disabled in offline mode.")

    # --- Tests for select_default_model ---

    @patch("aider.onboarding.try_to_select_default_model", return_value="ollama/llama3")
    @patch("aider.onboarding.offer_openrouter_oauth")
    def test_select_default_model_already_specified(self, mock_offer_oauth, mock_try_select):
        """Test select_default_model returns args.model if provided."""
        args = argparse.Namespace(model="specific-model")
        io_mock = DummyIO()
        analytics_mock = DummyAnalytics()
        selected_model = select_default_model(args, io_mock, analytics_mock)
        self.assertEqual(selected_model, "specific-model")
        mock_try_select.assert_not_called()
        mock_offer_oauth.assert_not_called()

    @patch("aider.onboarding.try_to_select_default_model", return_value="ollama/llama3")
    @patch("aider.onboarding.offer_openrouter_oauth")
    def test_select_default_model_found_via_env(self, mock_offer_oauth, mock_try_select):
        """Test select_default_model returns model found by try_to_select."""
        args = argparse.Namespace(model=None)  # No model specified
        io_mock = DummyIO()
        io_mock.tool_warning = MagicMock()  # Track warnings
        analytics_mock = DummyAnalytics()
        analytics_mock.event = MagicMock()  # Track events

        selected_model = select_default_model(args, io_mock, analytics_mock)

        self.assertEqual(selected_model, "ollama/llama3")
        mock_try_select.assert_called_once()
        io_mock.tool_warning.assert_called_once_with(
            "Using ollama/llama3 model with API key from environment."
        )
        analytics_mock.event.assert_called_once_with("auto_model_selection", model="ollama/llama3")
        mock_offer_oauth.assert_not_called()

    # OFFLINE FORK: OAuth is disabled, so select_default_model should not offer OAuth
    @patch(
        "aider.onboarding.try_to_select_default_model", return_value=None
    )
    @patch(
        "aider.onboarding.offer_openrouter_oauth", return_value=False
    )
    def test_select_default_model_no_keys_offline(self, mock_offer_oauth, mock_try_select):
        """Test select_default_model does not offer OAuth in offline mode."""
        args = argparse.Namespace(model=None)
        io_mock = DummyIO()
        io_mock.tool_warning = MagicMock()
        io_mock.offer_url = MagicMock()
        analytics_mock = DummyAnalytics()

        selected_model = select_default_model(args, io_mock, analytics_mock)

        self.assertIsNone(selected_model)
        self.assertEqual(mock_try_select.call_count, 2)  # Called before and after oauth attempt
        mock_offer_oauth.assert_called_once()  # Still called but returns False immediately
        io_mock.tool_warning.assert_called_once_with(
            "No LLM model was specified and no API keys were provided."
        )
        io_mock.offer_url.assert_called_once()  # Should offer docs URL

    # --- Tests for offer_openrouter_oauth ---
    # OFFLINE FORK: offer_openrouter_oauth always returns False
    def test_offer_openrouter_oauth_disabled(self):
        """Test offer_openrouter_oauth is disabled in offline mode."""
        io_mock = DummyIO()
        io_mock.confirm_ask = MagicMock(return_value=True)  # User says yes
        analytics_mock = DummyAnalytics()
        analytics_mock.event = MagicMock()

        result = offer_openrouter_oauth(io_mock, analytics_mock)

        self.assertFalse(result)
        io_mock.confirm_ask.assert_not_called()
        analytics_mock.event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
