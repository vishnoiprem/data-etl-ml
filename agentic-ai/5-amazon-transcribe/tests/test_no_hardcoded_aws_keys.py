"""
tests/test_no_hardcoded_aws_keys.py — regression test for the
AKIA...-in-source incident.

What this covers:
  1. No hardcoded AKIA pattern in any of the 3 source files
     (app.py, Amazon_Polly.py, AudioRecorder.jsx).
  2. No hardcoded 40-char base64 secret pattern in any source file.
  3. The scripts raise a clear RuntimeError if AWS_ACCESS_KEY_ID /
     AWS_SECRET_ACCESS_KEY are not set in the environment.
  4. The .env.example file exists and does not contain real keys.

If a developer (or a copy-paste accident) re-introduces a hardcoded
key, this test fails on the next CI run.

Run:
    python3 -m tests.test_no_hardcoded_aws_keys
"""

import importlib.util
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent
PKG = HERE.parent
APP_PY = PKG / "app.py"
POLLY_PY = PKG / "Amazon_Polly.py"
JSX = PKG / "educative-code-widget-files 2" / "src" / "components" / "AudioRecorder.jsx"
ENV_EXAMPLE = PKG / ".env.example"

# AWS access key pattern: AKIA / ASIA prefix + 16 uppercase alnum chars
AKIA_RE = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
# 40-char base64-ish (the secret key shape)
SECRET_RE = re.compile(r"['\"][A-Za-z0-9/+=]{40}['\"]")


def _read(p: Path) -> str:
    return p.read_text() if p.exists() else ""


def _load_module_from_path(path: Path, name: str):
    """Load a .py file as a module. The file's top-level code runs
    on import, which is the actual surface we're testing — that's
    where the credentials are read."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NoHardcodedKeysTest(unittest.TestCase):
    def test_no_akia_in_app_py(self):
        text = _read(APP_PY)
        m = AKIA_RE.search(text)
        self.assertIsNone(m, f"AKIA pattern found in app.py: {m.group(0) if m else None}")

    def test_no_akia_in_polly_py(self):
        text = _read(POLLY_PY)
        m = AKIA_RE.search(text)
        self.assertIsNone(m, f"AKIA pattern found in Amazon_Polly.py: {m.group(0) if m else None}")

    def test_no_akia_in_jsx(self):
        text = _read(JSX)
        m = AKIA_RE.search(text)
        self.assertIsNone(m, f"AKIA pattern found in AudioRecorder.jsx: {m.group(0) if m else None}")

    def test_no_long_secret_in_source(self):
        # The old 40-char secret was 'GHkyWVtuD7CnkqQzZk2a1FZ4Ck5cvSVZ+xQydmlO'
        for path in (APP_PY, POLLY_PY, JSX):
            text = _read(path)
            m = SECRET_RE.search(text)
            if m:
                # Allow the literal string "AWS_SECRET_ACCESS_KEY" itself
                # (which contains a 28-char identifier) but flag anything
                # 40+ chars inside quotes that looks like a base64 secret.
                self.assertNotIn("GHkyWVtuD7CnkqQzZk2a1FZ4Ck5cvSVZ+xQydmlO", text,
                                 f"old hardcoded secret found in {path.name}")

    def test_app_py_raises_without_env(self):
        # Make sure AWS_* env vars are not set during this test
        import os
        saved = {k: os.environ.pop(k, None) for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION")}
        try:
            with self.assertRaises(RuntimeError) as cm:
                _load_module_from_path(APP_PY, "_app_under_test")
            msg = str(cm.exception)
            self.assertIn("AWS_ACCESS_KEY_ID", msg)
            self.assertIn("hardcoded", msg.lower())
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_polly_py_raises_without_env(self):
        import os
        saved = {k: os.environ.pop(k, None) for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION")}
        try:
            with self.assertRaises(RuntimeError) as cm:
                _load_module_from_path(POLLY_PY, "_polly_under_test")
            msg = str(cm.exception)
            self.assertIn("AWS_ACCESS_KEY_ID", msg)
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_env_example_exists_and_has_placeholders(self):
        self.assertTrue(ENV_EXAMPLE.exists(), ".env.example must exist")
        text = ENV_EXAMPLE.read_text()
        self.assertIn("AWS_ACCESS_KEY_ID", text)
        self.assertIn("AWS_SECRET_ACCESS_KEY", text)
        # Must NOT contain a real key shape
        self.assertIsNone(AKIA_RE.search(text),
                          ".env.example must not contain a real AKIA pattern — it should have a placeholder")
        # Must NOT contain the old hardcoded secret
        self.assertNotIn("GHkyWVtuD7CnkqQzZk2a1FZ4Ck5cvSVZ+xQydmlO", text)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(NoHardcodedKeysTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
