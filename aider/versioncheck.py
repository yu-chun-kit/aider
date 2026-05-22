import os
import sys
import time
from pathlib import Path

import packaging.version

import aider
from aider import utils
from aider.dump import dump  # noqa: F401

VERSION_CHECK_FNAME = Path.home() / ".aider" / "caches" / "versioncheck"


def install_from_main_branch(io):
    """
    Install the latest version of aider from the main branch of the GitHub repository.
    """
    io.tool_error("--install-main-branch is disabled in offline mode.")
    return False


def install_upgrade(io, latest_version=None):
    """
    Install the latest version of aider from PyPI.
    """
    io.tool_error("--upgrade is disabled in offline mode.")
    return False


def check_version(io, just_check=False, verbose=False):
    io.tool_error("--check-update is disabled in offline mode.")
    return False
