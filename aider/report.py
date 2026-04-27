import os
import platform
import subprocess
import sys
import traceback
import urllib.parse
import webbrowser

from aider import __version__
from aider.urls import github_issues
from aider.versioncheck import VERSION_CHECK_FNAME

FENCE = "`" * 3


def get_python_info():
    implementation = platform.python_implementation()
    is_venv = sys.prefix != sys.base_prefix
    return (
        f"Python implementation: {implementation}\nVirtual environment:"
        f" {'Yes' if is_venv else 'No'}"
    )


def get_os_info():
    return f"OS: {platform.system()} {platform.release()} ({platform.architecture()[0]})"


def get_git_info():
    try:
        git_version = subprocess.check_output(["git", "--version"]).decode().strip()
        return f"Git version: {git_version}"
    except Exception:
        return "Git information unavailable"


def report_github_issue(issue_text, title=None, confirm=True):
    # OFFLINE FORK: disabled to prevent opening browser / external URLs
    print("Bug reporting is disabled in offline fork.")
    return


def exception_handler(exc_type, exc_value, exc_traceback):
    # If it's a KeyboardInterrupt, just call the default handler
    if issubclass(exc_type, KeyboardInterrupt):
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # We don't want any more exceptions
    sys.excepthook = None

    # Check if VERSION_CHECK_FNAME exists and delete it if so
    try:
        if VERSION_CHECK_FNAME.exists():
            VERSION_CHECK_FNAME.unlink()
    except Exception:
        pass  # Swallow any errors

    # Format the traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)

    # Replace full paths with basenames in the traceback
    tb_lines_with_basenames = []
    for line in tb_lines:
        try:
            if "File " in line:
                parts = line.split('"')
                if len(parts) > 1:
                    full_path = parts[1]
                    basename = os.path.basename(full_path)
                    line = line.replace(full_path, basename)
        except Exception:
            pass
        tb_lines_with_basenames.append(line)

    tb_text = "".join(tb_lines_with_basenames)

    # Find the innermost frame
    innermost_tb = exc_traceback
    while innermost_tb.tb_next:
        innermost_tb = innermost_tb.tb_next

    # Get the filename and line number from the innermost frame
    filename = innermost_tb.tb_frame.f_code.co_filename
    line_number = innermost_tb.tb_lineno
    try:
        basename = os.path.basename(filename)
    except Exception:
        basename = filename

    # Get the exception type name
    exception_type = exc_type.__name__

    # Prepare the issue text
    issue_text = f"An uncaught exception occurred:\n\n{FENCE}\n{tb_text}\n{FENCE}"

    # Prepare the title
    title = f"Uncaught {exception_type} in {basename} line {line_number}"

    # Report the issue
    report_github_issue(issue_text, title=title)

    # Call the default exception handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def report_uncaught_exceptions():
    """
    Set up the global exception handler to report uncaught exceptions.
    """
    sys.excepthook = exception_handler


def dummy_function1():
    def dummy_function2():
        def dummy_function3():
            raise ValueError("boo")

        dummy_function3()

    dummy_function2()


def main():
    report_uncaught_exceptions()

    dummy_function1()

    title = None
    if len(sys.argv) > 2:
        # Use the first command-line argument as the title and the second as the issue text
        title = sys.argv[1]
        issue_text = sys.argv[2]
    elif len(sys.argv) > 1:
        # Use the first command-line argument as the issue text
        issue_text = sys.argv[1]
    else:
        # Read from stdin if no argument is provided
        print("Enter the issue title (optional, press Enter to skip):")
        title = input().strip()
        if not title:
            title = None
        print("Enter the issue text (Ctrl+D to finish):")
        issue_text = sys.stdin.read().strip()

    report_github_issue(issue_text, title)


if __name__ == "__main__":
    main()
