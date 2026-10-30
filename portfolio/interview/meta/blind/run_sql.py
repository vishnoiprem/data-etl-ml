"""Test harness: loads schema.sql, runs every numbered .sql file, and checks
the result against the file's expected rows.

For each file N_*.sql we expect:
    -- Solution ...
    <SQL>
    -- Expected output ...
    -- (row, as, a, python, tuple)     <- one line per expected row
    -- Talk-track follow-ups ...

The SQL files use MySQL syntax. SQLite has no DATEDIFF, so we register one
that behaves like MySQL's DATEDIFF(later, earlier) -> whole days.
"""
import ast
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
schema = (ROOT / "schema.sql").read_text()

sql_files = sorted(ROOT.glob("[0-9]*.sql"), key=lambda p: int(p.name.split("_")[0]))
print(f"Found {len(sql_files)} SQL solution files.\n")


def datediff(later: str, earlier: str) -> int | None:
    """MySQL DATEDIFF(later, earlier): whole days between two dates."""
    if later is None or earlier is None:
        return None
    return (date.fromisoformat(later[:10]) - date.fromisoformat(earlier[:10])).days


def extract_query(text: str) -> str | None:
    """The SQL between the '-- Solution' marker and '-- Expected output'."""
    if not re.search(r"^-- Solution", text, re.MULTILINE):
        return None
    after = re.split(r"^-- Solution.*$", text, maxsplit=1, flags=re.MULTILINE)[1]
    after = re.split(r"^-- Expected output", after, maxsplit=1, flags=re.MULTILINE)[0]
    return after.strip().rstrip(";").strip()


def extract_expected(text: str) -> list[tuple] | None:
    """Rows written as '-- (...)' in the Expected output section."""
    parts = re.split(r"^-- Expected output.*$", text, maxsplit=1, flags=re.MULTILINE)
    if len(parts) < 2:
        return None
    section = re.split(r"^-- Talk-track", parts[1], maxsplit=1, flags=re.MULTILINE)[0]
    rows = []
    for line in section.splitlines():
        m = re.match(r"^-- (\(.*\))\s*$", line)
        if not m:
            continue
        try:
            row = ast.literal_eval(m.group(1))
        except (ValueError, SyntaxError):
            continue  # prose in parentheses, not a row
        rows.append(row if isinstance(row, tuple) else (row,))
    return rows or None


def normalize(row: tuple) -> tuple:
    """Round floats so 13.138888888888889 == 13.13888888888889."""
    return tuple(round(v, 2) if isinstance(v, float) else v for v in row)


failures = 0
for sql_file in sql_files:
    print(f"=== {sql_file.name} ===")
    text = sql_file.read_text()
    query = extract_query(text)
    if query is None:
        print("  (could not find -- Solution section)\n")
        failures += 1
        continue

    conn = sqlite3.connect(":memory:")
    conn.create_function("DATEDIFF", 2, datediff)
    conn.executescript(schema)
    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.Error as e:
        print(f"  ERROR: {e}\n")
        failures += 1
        conn.close()
        continue
    conn.close()

    for row in rows:
        print(" ", row)
    expected = extract_expected(text)
    if expected is None:
        print("  (no expected rows to check)")
    elif [normalize(r) for r in rows] == [normalize(r) for r in expected]:
        print("  PASS")
    else:
        print("  FAIL — expected:")
        for row in expected:
            print("   ", row)
        failures += 1
    print()

print("All SQL files match their expected output." if not failures
      else f"{failures} SQL file(s) failed.")
sys.exit(1 if failures else 0)
