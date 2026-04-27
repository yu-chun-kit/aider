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
    # OFFLINE FORK: disabled to prevent external network requests
    return False


def install_upgrade(io, latest_version=None):
    """
    Install the latest version of aider from PyPI.
    """
    # OFFLINE FORK: disabled to prevent external network requests
    return False


def check_version(io, just_check=False, verbose=False):
    # OFFLINE FORK: disabled to prevent external network requests
    if verbose:
        io.tool_output("Version checking is disabled in offline fork.")
    return False
