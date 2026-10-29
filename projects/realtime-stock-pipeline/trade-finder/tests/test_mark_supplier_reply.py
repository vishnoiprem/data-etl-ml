"""
tests/test_mark_supplier_reply.py — verify the supplier reply CLI
against a synthetic state JSON (no real file I/O outside tmpdir).

The CLI persists to data/supplier_state.json. We patch STATE_FILE
to point at a tmp path so the test never touches the real
trade-finder data.
"""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
BIN = HERE.parent / "mark_supplier_reply.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "mark_supplier_reply", BIN
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MarkSupplierReplyTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()
        self.tmp = Path(tempfile.mkdtemp(prefix="mark_supplier_test_"))
        self.fake_state = self.tmp / "supplier_state.json"
        # Patch the module's STATE_FILE constant
        self.orig_state = self.mod.STATE_FILE
        self.mod.STATE_FILE = self.fake_state

    def tearDown(self):
        self.mod.STATE_FILE = self.orig_state
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *args: str) -> int:
        saved = sys.argv[:]
        sys.argv = ["mark_supplier_reply.py", *args]
        try:
            return self.mod.main()
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 2
        except Exception:
            return "exception"
        finally:
            sys.argv = saved

    def _state(self) -> dict:
        return json.loads(self.fake_state.read_text()) if self.fake_state.exists() else {}

    def test_alias_resolution(self):
        # "Gold Star" → canonical 1. Shenzhen Gold Star Technology
        self.assertIn("1. Shenzhen Gold Star", self.mod._resolve_supplier("Gold Star"))
        self.assertIn("2. Shenzhen OCOM", self.mod._resolve_supplier("OCOM"))
        self.assertIn("3. Shenzhen Qiyang", self.mod._resolve_supplier("Qiyang"))
        # Also case-insensitive
        self.assertIn("1. Shenzhen Gold Star", self.mod._resolve_supplier("goldstar"))
        # Unknown raises
        with self.assertRaises(ValueError):
            self.mod._resolve_supplier("MadeUpSupplier")

    def test_replied_writes_state(self):
        rc = self._run("Gold Star", "--replied", "--at", "2026-10-15", "--via", "email")
        self.assertEqual(rc, 0)
        s = self._state()
        self.assertIn("1. Shenzhen Gold Star Technology", s)
        self.assertEqual(s["1. Shenzhen Gold Star Technology"]["replied_at"], "2026-10-15")
        self.assertEqual(s["1. Shenzhen Gold Star Technology"]["replied_via"], "email")

    def test_sample_lifecycle(self):
        self._run("OCOM", "--sample-ordered", "--at", "2026-10-17")
        self._run("OCOM", "--sample-shipped", "--at", "2026-10-19")
        self._run("OCOM", "--sample-received", "--at", "2026-10-24")
        self._run("OCOM", "--sample-qc-pass", "--at", "2026-10-31")
        s = self._state()["2. Shenzhen OCOM Technology"]
        self.assertEqual(s["sample_ordered"], "2026-10-17")
        self.assertEqual(s["sample_shipped"], "2026-10-19")
        self.assertEqual(s["sample_received"], "2026-10-24")
        self.assertEqual(s["sample_qc"], "pass")

    def test_notes_appended(self):
        self._run("Qiyang", "--replied", "--at", "2026-10-15", "--via", "email",
                  "--notes", "Quoted $8.50/500u, 19d lead, T/T 30/70 OK")
        self._run("Qiyang", "--replied", "--at", "2026-10-15", "--via", "email",
                  "--notes", "OEM MOQ 500u, tooling $800")
        s = self._state()["3. Shenzhen Qiyang Technology"]
        # Both notes should be present, newest last
        self.assertIn("Quoted $8.50/500u", s["notes"])
        self.assertIn("OEM MOQ 500u", s["notes"])

    def test_revert_clears_supplier(self):
        self._run("Gold Star", "--replied", "--at", "2026-10-15")
        self.assertIn("1. Shenzhen Gold Star Technology", self._state())
        rc = self._run("Gold Star", "--revert")
        self.assertEqual(rc, 0)
        self.assertNotIn("1. Shenzhen Gold Star Technology", self._state())

    def test_invalid_channel_rejected(self):
        rc = self._run("Gold Star", "--replied", "--via", "fax")
        self.assertNotEqual(rc, 0)
        self.assertEqual(self._state(), {}, "no state should be written on invalid channel")

    def test_no_action_rejected(self):
        # A query with no outcome flag should fail
        rc = self._run("Gold Star")
        self.assertNotEqual(rc, 0)
        self.assertEqual(self._state(), {})

    def test_list_does_not_modify(self):
        before = self.fake_state.read_bytes() if self.fake_state.exists() else b""
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self._run("--list")
        finally:
            sys.stdout = saved_stdout
        after = self.fake_state.read_bytes() if self.fake_state.exists() else b""
        self.assertEqual(before, after, "--list must not modify state")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(MarkSupplierReplyTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
