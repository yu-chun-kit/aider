import os
import unittest
from unittest.mock import patch

from aider.main import main


class TestBrowser(unittest.TestCase):
    @patch("aider.main.launch_gui")
    def test_browser_flag_disabled_offline(self, mock_launch_gui):
        """OFFLINE FORK: browser mode is disabled and should not launch GUI."""
        os.environ["AIDER_ANALYTICS"] = "false"

        # Run main with --browser and --yes flags
        result = main(["--browser", "--yes"])

        # Check that launch_gui was NOT called in offline mode
        mock_launch_gui.assert_not_called()

        # The function should return without error
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
