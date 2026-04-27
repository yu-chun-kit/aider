import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from aider.analytics import Analytics


@pytest.fixture
def temp_analytics_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_data_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        yield temp_dir


def test_analytics_initialization(temp_data_dir):
    analytics = Analytics(permanently_disable=True)
    assert analytics.mp is None
    assert analytics.ph is None
    assert analytics.permanently_disable is True
    assert analytics.user_id is not None


def test_analytics_enable_disable(temp_data_dir):
    analytics = Analytics()
    analytics.asked_opt_in = True

    analytics.enable()
    # OFFLINE FORK: analytics is hard-disabled, ph remains None
    # assert analytics.mp is not None
    # assert analytics.ph is not None

    analytics.disable(permanently=False)
    assert analytics.mp is None
    assert analytics.ph is None
    # OFFLINE FORK: disable(True) is called in __init__, so permanently_disable is already True
    # assert analytics.permanently_disable is not True

    analytics.disable(permanently=True)
    assert analytics.permanently_disable is True


def test_analytics_data_persistence(temp_data_dir):
    analytics1 = Analytics()
    user_id = analytics1.user_id

    analytics2 = Analytics()
    assert analytics2.user_id == user_id


def test_analytics_event_logging(temp_analytics_file, temp_data_dir):
    analytics = Analytics(logfile=temp_analytics_file)
    analytics.asked_opt_in = True
    analytics.enable()

    test_event = "test_event"
    test_properties = {"test_key": "test_value"}

    # OFFLINE FORK: event() returns immediately, no network calls
    analytics.event(test_event, **test_properties)

    # Verify logfile is still written even in offline fork
    with open(temp_analytics_file) as f:
        log_entry = json.loads(f.read().strip())
        assert log_entry["event"] == test_event
        assert "test_key" in log_entry["properties"]


def test_system_info(temp_data_dir):
    analytics = Analytics()
    sys_info = analytics.get_system_info()

    assert "python_version" in sys_info
    assert "os_platform" in sys_info
    assert "os_release" in sys_info
    assert "machine" in sys_info


def test_need_to_ask(temp_data_dir):
    analytics = Analytics()
    # OFFLINE FORK: analytics is hard-disabled in __init__, so need_to_ask always returns False
    assert analytics.need_to_ask(True) is False
    assert analytics.need_to_ask(False) is False

    # Temporarily re-enable for testing the percentage logic
    analytics.permanently_disable = False
    analytics.asked_opt_in = False
    analytics.user_id = "000"
    assert analytics.need_to_ask(None) is True

    analytics.asked_opt_in = True
    assert analytics.need_to_ask(True) is False

    analytics.permanently_disable = True
    assert analytics.need_to_ask(True) is False


def test_is_uuid_in_percentage():
    from aider.analytics import is_uuid_in_percentage

    # Test basic percentage thresholds
    assert is_uuid_in_percentage("00000000000000000000000000000000", 1) is True
    assert is_uuid_in_percentage("01999000000000000000000000000000", 1) is True
    assert is_uuid_in_percentage("02000000000000000000000000000000", 1) is True
    assert is_uuid_in_percentage("02910000000000000000000000000001", 1) is False
    assert is_uuid_in_percentage("03000000000000000000000000000000", 1) is False
    assert is_uuid_in_percentage("ff000000000000000000000000000000", 1) is False

    assert is_uuid_in_percentage("00000000000000000000000000000000", 10) is True
    assert is_uuid_in_percentage("19000000000000000000000000000000", 10) is True
    assert is_uuid_in_percentage("1a000000000000000000000000000000", 10) is False
    assert is_uuid_in_percentage("ff000000000000000000000000000000", 10) is False

    # Test edge cases
    assert is_uuid_in_percentage("00000000000000000000000000000000", 0) is False
    assert is_uuid_in_percentage("00000000000000000000000000000000", 100) is True
    assert is_uuid_in_percentage("ffffffffffffffffffffffffffffffff", 100) is True

    # Test invalid inputs
    with pytest.raises(ValueError):
        is_uuid_in_percentage("00000000000000000000000000000000", -1)
    with pytest.raises(ValueError):
        is_uuid_in_percentage("00000000000000000000000000000000", 101)

    # Test empty/None UUID
    assert is_uuid_in_percentage("", 50) is False
    assert is_uuid_in_percentage(None, 50) is False
