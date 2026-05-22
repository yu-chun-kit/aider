import tempfile
from pathlib import Path

from scripts import verify_offline


def _write_sample(contents):
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "sample.py"
        source.write_text(contents.lstrip(), encoding="utf-8")
        yield source


def test_func_body_finds_module_level_function():
    for source in _write_sample(
        """
def hello():
    return 'hi'
"""
    ):
        body = verify_offline._func_body(source, "hello")
    assert "return 'hi'" in body


def test_func_body_finds_class_method_with_qualified_name():
    for source in _write_sample(
        """
class Analytics:
    def __init__(self):
        self.permanently_disable = True
"""
    ):
        body = verify_offline._func_body(source, "Analytics.__init__")
    assert "permanently_disable = True" in body


def test_func_body_finds_nested_class_method_with_qualified_name():
    for source in _write_sample(
        """
class Outer:
    class ModelInfoManager:
        def _update_cache(self):
            pass
"""
    ):
        body = verify_offline._func_body(source, "Outer.ModelInfoManager._update_cache")
    assert "pass" in body
