from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

from pipeline_logic import should_run_full_load

# The helper defined in the previous cell is still in the namespace.
def test_should_run_full_load(row_count, threshold, expected):
    """The full-load decision must be a strict greater-than."""
    actual = should_run_full_load(row_count, threshold)
    assert actual == expected, f"expected {expected}, got {actual}"


CASES = [
    (0, 100, False),
    (99, 100, False),
    (100, 100, False),   # boundary: NOT greater than
    (101, 100, True),
    (5000, 100, True),
]

passed = 0
for case in CASES:
    try:
        test_should_run_full_load(*case)
        passed += 1
        print(f"    PASS  test_should_run_full_load{case}")
    except AssertionError as exc:
        print(f"    FAIL  test_should_run_full_load{case}: {exc}")

print()
print(f"{passed}/{len(CASES)} cases passed")
print()
print("The boundary case (100, 100) is the one that catches the")
print("off-by-one between '>' and '>='.")
