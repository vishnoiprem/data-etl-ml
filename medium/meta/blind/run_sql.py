"""Test harness: loads schema.sql, runs every numbered .sql file, prints results.

For each file N_*.sql we expect:
    -- Solution\n-- <one or more dashes>\n<SQL>\n
followed by -- Expected output that ends the executable portion.
"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent
schema = (ROOT / "schema.sql").read_text()

sql_files = sorted(ROOT.glob("[0-9]*.sql"))
print(f"Found {len(sql_files)} SQL solution files.\n")


def extract_query(text: str) -> str | None:
    """Find the first SQL block after a '-- Solution' marker."""
    # Find lines starting with '-- Solution' followed eventually by a SQL statement.
    # Solution markers may include parenthetical notes.
    if not re.search(r"^-- Solution", text, re.MULTILINE):
        return None
    # Find the first SQL statement after the Solution marker, stopping at
    # the first -- Expected output line.
    after = re.split(r"^-- Solution.*$", text, maxsplit=1, flags=re.MULTILINE)[1]
    # Cut off at "Expected output"
    after = re.split(r"^-- Expected output", after, maxsplit=1, flags=re.MULTILINE)[0]
    # Strip any pure-comment lines and blank lines at the start.
    return after.strip()


for sql_file in sql_files:
    print(f"=== {sql_file.name} ===")
    query = extract_query(sql_file.read_text())
    if query is None:
        print("  (could not find -- Solution section)\n")
        continue
    query = query.rstrip(";").strip()

    conn = sqlite3.connect(":memory:")
    conn.executescript(schema)
    try:
        rows = conn.execute(query).fetchall()
        for row in rows:
            print(" ", row)
    except sqlite3.Error as e:
        print(f"  ERROR: {e}")
    conn.close()
    print()
