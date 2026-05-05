from pathlib import Path

from scripts import verify_offline


def test_func_body_finds_module_level_function(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        """

def hello():
    return 'hi'
""".lstrip(),
        encoding="utf-8",
    )

    body = verify_offline._func_body(source, "hello")

    assert "return 'hi'" in body


def test_func_body_finds_class_method_with_qualified_name(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        """
class Analytics:
    def __init__(self):
        self.permanently_disable = True
""".lstrip(),
        encoding="utf-8",
    )

    body = verify_offline._func_body(source, "Analytics.__init__")

    assert "permanently_disable = True" in body


def test_func_body_finds_nested_class_method_with_qualified_name(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        """
class Outer:
    class ModelInfoManager:
        def _update_cache(self):
            pass
""".lstrip(),
        encoding="utf-8",
    )

    body = verify_offline._func_body(source, "Outer.ModelInfoManager._update_cache")

    assert "pass" in body
