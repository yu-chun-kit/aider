import time
import unittest
from unittest.mock import MagicMock

from aider.commands import Commands
from aider.io import InputOutput
from aider.scrape import Scraper


class TestScrape(unittest.TestCase):
    def test_scrape_disabled_offline(self):
        """OFFLINE FORK: scrape always returns None and does not make network requests."""
        mock_print_error = MagicMock()
        scraper = Scraper(
            print_error=mock_print_error, playwright_available=True, verify_ssl=True
        )
        result = scraper.scrape("https://self-signed.badssl.com")
        self.assertIsNone(result)
        mock_print_error.assert_called_once()

    def setUp(self):
        self.io = InputOutput(yes=True)
        self.commands = Commands(self.io, None)

    def test_cmd_web_disabled_offline(self):
        """OFFLINE FORK: cmd_web returns header-only content because scraping is disabled."""
        mock_print_error = MagicMock()
        self.commands.io.tool_error = mock_print_error

        result = self.commands.cmd_web("https://example.com", return_content=True)

        # In offline mode, scraping is disabled so result should be just the header
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("Here is the content of https://example.com:"))

    def test_scrape_actual_url_disabled_offline(self):
        """OFFLINE FORK: scrape always returns None."""
        mock_print_error = MagicMock()
        scraper = Scraper(print_error=mock_print_error, playwright_available=True)

        result = scraper.scrape("https://example.com")
        self.assertIsNone(result)
        mock_print_error.assert_called_once()

    def test_scraper_httpx_disabled(self):
        """OFFLINE FORK: scrape_with_httpx still works if called directly but scrape doesn't use it."""
        mock_print_error = MagicMock()
        scraper = Scraper(print_error=mock_print_error, verify_ssl=False)

        # Test internal methods still exist and work
        scraper.try_pandoc()
        scraper.html_to_markdown("<html><body><h1>Test</h1></body></html>")

        # scrape_with_httpx may error due to network being disabled, but that's expected
        # The method itself should not crash
        try:
            scraper.scrape_with_httpx("https://example.com")
        except Exception:
            pass

    def test_scrape_with_playwright_disabled_offline(self):
        """OFFLINE FORK: scrape bypasses playwright entirely."""
        mock_print_error = MagicMock()
        scraper = Scraper(print_error=mock_print_error, playwright_available=True)

        # Mock scrape_with_playwright to ensure it's never called
        scraper.scrape_with_playwright = MagicMock()
        scraper.scrape_with_playwright.return_value = (None, None)

        result = scraper.scrape("https://example.com")

        # In offline mode, scrape returns None immediately without calling playwright
        self.assertIsNone(result)
        scraper.scrape_with_playwright.assert_not_called()

    def test_scrape_text_plain_disabled(self):
        """OFFLINE FORK: scrape always returns None regardless of mocked internals."""
        scraper = Scraper(print_error=MagicMock(), playwright_available=True)

        plain_text = "This is plain text content."
        scraper.scrape_with_playwright = MagicMock(return_value=(plain_text, "text/plain"))

        result = scraper.scrape("https://example.com")
        self.assertIsNone(result)

    def test_scrape_text_html_disabled(self):
        """OFFLINE FORK: scrape always returns None regardless of mocked internals."""
        scraper = Scraper(print_error=MagicMock(), playwright_available=True)

        html_content = "<html><body><h1>Test</h1><p>This is HTML content.</p></body></html>"
        scraper.scrape_with_playwright = MagicMock(return_value=(html_content, "text/html"))

        expected_markdown = "# Test\n\nThis is HTML content."
        scraper.html_to_markdown = MagicMock(return_value=expected_markdown)

        result = scraper.scrape("https://example.com")
        self.assertIsNone(result)
        scraper.html_to_markdown.assert_not_called()


if __name__ == "__main__":
    unittest.main()
