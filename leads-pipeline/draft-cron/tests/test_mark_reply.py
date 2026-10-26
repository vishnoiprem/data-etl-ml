"""
tests/test_mark_reply.py — verify bin/mark_reply.py behaves correctly
against a synthetic leads-tracker.csv.

What this covers:
  1. Idempotent column migration: running on a CSV without the four
     reply columns adds them, doesn't fail.
  2. --replied updates the right row by company substring.
  3. --meeting sets the meeting column.
  4. --revert clears the reply state.
  5. --via validates against the channel whitelist.
  6. Query miss raises a clean ValueError.

The test loads bin/mark_reply.py as a module, monkey-patches
`find_latest_tracker` to return our synthetic path, and invokes
`main()` with sys.argv. This way the test never touches the real
leads-pipeline/2026-10-10/leads-tracker.csv.
"""

import csv
import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
BIN = HERE.parent / "bin" / "mark_reply.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("mark_reply", BIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_synthetic_tracker(tmp: Path, date_str: str = "2099-01-15") -> Path:
    drop = tmp / date_str
    drop.mkdir()
    csv_path = drop / "leads-tracker.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "tier", "date_sent", "channel", "company", "handle", "role", "rate",
            "stack", "remote_policy", "posted_date", "apply_link", "cover_letter",
            "status", "notes",
        ])
        w.writerow([
            "1", "2099-01-10", "email", "Acme Co", "@acme",
            "Senior AI Engineer", "$80-120/hr", "Python LLMs", "Worldwide",
            "2099-01-08", "https://example.com/acme", "Hi Acme — Vietnam pod...",
            "⬜", "open in browser",
        ])
        w.writerow([
            "1", "2099-01-10", "x_dm", "BetaFounder", "@betafounder",
            "Founding Engineer", "$90-150/hr", "TS agents", "DM open",
            "2099-01-09", "https://x.com/betafounder", "Hey — congrats...",
            "⬜", "DM from X account",
        ])
    return csv_path


class MarkReplyTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()
        self.tmp = Path(tempfile.mkdtemp(prefix="mark_reply_test_"))
        self.tracker = _make_synthetic_tracker(self.tmp)
        # Monkey-patch find_latest_tracker to always return our synthetic CSV
        self.orig_find = self.mod.find_latest_tracker
        self.mod.find_latest_tracker = lambda: self.tracker

    def tearDown(self):
        self.mod.find_latest_tracker = self.orig_find
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *args: str) -> int:
        """Invoke mod.main() with sys.argv set. Returns the exit code,
        or 'exception' if main() raised (SystemExit not caught here)."""
        saved = sys.argv[:]
        sys.argv = ["mark_reply.py", *args]
        try:
            return self.mod.main()
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 2
        except Exception:
            return "exception"
        finally:
            sys.argv = saved

    def _capture(self, *args: str) -> tuple[int, str]:
        saved = sys.argv[:]
        sys.argv = ["mark_reply.py", *args]
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = self.mod.main()
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 2
        finally:
            sys.argv = saved
        return rc, buf.getvalue()

    def _read(self):
        with self.tracker.open() as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        return header, rows

    def test_idempotent_column_add(self):
        rc = self._run("Acme", "--replied", "--at", "2099-01-12", "--via", "email")
        self.assertEqual(rc, 0, f"expected 0, got {rc}")
        header, rows = self._read()
        self.assertEqual(len(header), 18, f"Expected 18 columns, got {len(header)}: {header}")
        acme = next(r for r in rows if r[3] == "Acme Co")
        self.assertEqual(acme[header.index("replied")], "yes")
        self.assertEqual(acme[header.index("replied_at")], "2099-01-12")
        self.assertEqual(acme[header.index("reply_channel")], "email")
        # BetaFounder row should be untouched
        beta = next(r for r in rows if r[3] == "BetaFounder")
        self.assertEqual(beta[header.index("replied")], "")

    def test_meeting_sets_meeting_column(self):
        rc = self._run("Beta", "--meeting", "--at", "2099-01-14")
        self.assertEqual(rc, 0)
        header, rows = self._read()
        beta = next(r for r in rows if r[3] == "BetaFounder")
        self.assertEqual(beta[header.index("meeting_booked")], "2099-01-14")

    def test_revert_clears_state(self):
        self.assertEqual(self._run("Acme", "--replied", "--at", "2099-01-12", "--via", "email"), 0)
        self.assertEqual(self._run("Acme", "--revert"), 0)
        header, rows = self._read()
        acme = next(r for r in rows if r[3] == "Acme Co")
        for col in ("replied", "replied_at", "reply_channel", "meeting_booked"):
            self.assertEqual(acme[header.index(col)], "", f"{col} should be cleared after revert")

    def test_invalid_channel_rejected(self):
        # argparse rejects unknown --via; the script's ap.error() raises SystemExit(2)
        rc = self._run("Acme", "--replied", "--via", "carrier_pigeon")
        self.assertNotEqual(rc, 0, "expected non-zero exit on invalid channel")
        # Also: the file should be unchanged (no migration happens because
        # argparse exits before the script touches the CSV).
        header, rows = self._read()
        self.assertEqual(len(header), 14, "CSV should be unchanged (still 14 cols) after invalid channel rejection")
        acme = next(r for r in rows if r[3] == "Acme Co")
        self.assertEqual(acme[12], "⬜", "status should still be the original emoji")

    def test_query_miss_raises(self):
        # ValueError from find_row; main() doesn't catch it → SystemExit(1)
        rc = self._run("NoSuchCompany", "--replied")
        self.assertNotEqual(rc, 0, "expected non-zero exit for query miss")

    def test_list_does_not_modify(self):
        before = self.tracker.read_bytes()
        rc, out = self._capture("--list")
        self.assertEqual(rc, 0)
        after = self.tracker.read_bytes()
        self.assertEqual(before, after, "--list must not modify the file")
        # And the output should mention our test companies
        self.assertIn("Acme Co", out)
        self.assertIn("BetaFounder", out)


def _print_results():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(MarkReplyTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    _print_results()
