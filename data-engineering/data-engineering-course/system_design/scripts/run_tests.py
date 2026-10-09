"""Run all tests for all modules — simple direct runner.

Each test file imports `from code.X import ...` where `code` is the
module's own code/ directory. We add the module dir to sys.path so
that import works, then run the test in-process. We also evict any
cached `code` module between modules so cross-contamination doesn't
happen.

Usage:
    python3 scripts/run_tests.py
    python3 scripts/run_tests.py 01_url_shortener
    python3 scripts/run_tests.py -v
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # system_design/

# Make `common` importable.
sys.path.insert(0, str(HERE))


def _evict_code() -> None:
    """Remove `code`, `service`, `app`, and any per-module cached
    modules so the next module's imports don't conflict.
    """
    blacklist = {
        "code", "service", "app", "tests",
        "trie",  # typeahead
    }
    for k in list(sys.modules.keys()):
        if k in blacklist or any(k.startswith(p + ".") for p in blacklist):
            del sys.modules[k]
    # Also evict anything that came from a previous module's path
    for k in list(sys.modules.keys()):
        mod = sys.modules[k]
        path = getattr(mod, "__file__", "") or ""
        if "/system_design/" in path and not path.startswith(str(HERE) + "/common"):
            del sys.modules[k]


def collect_tests(module_filter: str | None = None) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for module_dir in sorted(HERE.iterdir()):
        if not module_dir.is_dir() or not module_dir.name[:2].isdigit():
            continue
        if module_filter and module_dir.name != module_filter:
            continue
        tests_dir = module_dir / "tests"
        if not tests_dir.exists():
            continue
        _evict_code()
        # Add module dir + code dir to sys.path so `from code.X` resolves.
        sys.path.insert(0, str(module_dir))
        sys.path.insert(0, str(module_dir / "code"))
        try:
            for test_file in sorted(tests_dir.glob("test_*.py")):
                spec = importlib.util.spec_from_file_location(
                    f"_test_{module_dir.name}_{test_file.stem}",
                    test_file,
                )
                assert spec is not None and spec.loader is not None
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for name in dir(mod):
                    obj = getattr(mod, name)
                    if (isinstance(obj, type)
                            and issubclass(obj, unittest.TestCase)
                            and obj is not unittest.TestCase):
                        suite.addTests(
                            unittest.TestLoader().loadTestsFromTestCase(obj)
                        )
        finally:
            # Pop the paths we pushed
            try:
                sys.path.remove(str(module_dir))
            except ValueError:
                pass
            try:
                sys.path.remove(str(module_dir / "code"))
            except ValueError:
                pass
    return suite


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("module", nargs="?",
                   help="Run only this module (e.g. 01_url_shortener)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    suite = collect_tests(args.module)
    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
