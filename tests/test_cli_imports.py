import builtins
import importlib
import sys


def test_cli_imports_do_not_pull_pyside(monkeypatch):
    """Ensure CLI entrypoint stays free of GUI/PySide dependencies."""
    real_import = builtins.__import__

    def guard(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith(("PySide6", "sweeper.gui")):
            raise AssertionError(
                f"CLI should not import GUI/PySide6 modules (got {name})"
            )
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guard)
    sweeper_modules = {k: v for k, v in sys.modules.items() if k.startswith("sweeper")}
    try:
        for module_name in list(sys.modules.keys()):
            if module_name.startswith("sweeper"):
                sys.modules.pop(module_name, None)

        importlib.import_module("sweeper.cli.review")
        importlib.import_module("sweeper.cli.__main__")
    finally:
        for module_name in list(sys.modules.keys()):
            if module_name.startswith("sweeper") and module_name not in sweeper_modules:
                sys.modules.pop(module_name, None)
        sys.modules.update(sweeper_modules)
