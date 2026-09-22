"""Test runner for merge_strings_alternately.py"""
import sys
sys.path.insert(0, '/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/educative/pointer')
import merge_strings_alternately as m

solutions = [
    ("V1", m.merge_alt_v1),
    ("V2", m.merge_alt_v2),
    ("V3", m.merge_alt_v3),
    ("V4", m.merge_alt_v4),
    ("V5", m.merge_alt_v5),
    ("V6", m.merge_alt_v6),
    ("V7", m.merge_alt_v7),
    ("V8", m.merge_alt_v8),
    ("V9", m.merge_alt_v9),
    ("V10", m.merge_alt_v10),
]

test_cases = [
    ("abc", "pqr",    "apbqcr"),
    ("ab",  "pqrs",   "apbqrs"),
    ("abcd","pq",     "apbqcd"),
    ("",    "abc",    "abc"),
    ("abc", "",       "abc"),
    ("",    "",       ""),
    ("a",   "b",      "ab"),
    ("ab",  "cd",     "acbd"),
    ("wxyz","abc",    "waxbycz"),
    ("abc", "wxyz",   "awbxcyz"),
]

all_pass = True
for name, func in solutions:
    ok = True
    for idx, (w1, w2, expected) in enumerate(test_cases):
        try:
            got = func(w1, w2)
            if got != expected:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ({w1!r}, {w2!r}) -> {got!r} (expected {expected!r})")
        except Exception as e:
            ok = False
            all_pass = False
            print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
    if ok:
        print(f"  OK {name}: PASS")

print()
print("ALL PASS" if all_pass else "SOME FAILURES")
