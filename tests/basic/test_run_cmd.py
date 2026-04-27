import platform

import pytest  # noqa: F401

from aider.run_cmd import run_cmd


def test_run_cmd_echo():
    command = "echo Hello, World!"
    exit_code, output = run_cmd(command)

    assert exit_code == 0
    # Windows PowerShell echo outputs each arg on a separate line
    # and may include extra output from profile/modules
    if platform.system() == "Windows":
        assert "Hello" in output
        assert "World" in output
    else:
        assert output.strip() == "Hello, World!"
