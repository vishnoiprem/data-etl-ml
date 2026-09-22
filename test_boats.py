"""Test runner for boats_to_save_people.py"""
import sys
sys.path.insert(0, '/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/educative/11_Greedy_Techniques')
import boats_to_save_people as m

solutions = [
    ("V1", m.rescue_boats_v1),
    ("V2", m.rescue_boats_v2),
    ("V3", m.rescue_boats_v3),
    ("V4", m.rescue_boats_v4),
    ("V5", m.rescue_boats_v5),
    ("V6", m.rescue_boats_v6),
    ("V7", m.rescue_boats_v7),
    ("V8", m.rescue_boats_v8),
    ("V9", m.rescue_boats_v9),
    ("V10", m.rescue_boats_v10),
]

test_cases = [
    ([1, 2],                3, 1),
    ([3, 2, 2, 1],          3, 3),
    ([3, 5, 3, 4],          5, 4),
    ([1, 2, 3, 4],          5, 2),
    ([5, 1, 4, 2],          6, 2),
    ([1],                   1, 1),
    ([1, 1, 1, 1],          2, 2),
    ([2, 2],                6, 1),
    ([2, 2],                3, 2),
    ([3, 3, 3],             5, 3),
    ([3, 3, 3],             6, 2),
]

all_pass = True
for name, func in solutions:
    ok = True
    for people, limit, expected in test_cases:
        try:
            got = func(list(people), limit)
            if got != expected:
                ok = False
                all_pass = False
                print(f"  X {name}: people={people}, limit={limit} -> {got} (expected {expected})")
        except Exception as e:
            ok = False
            all_pass = False
            print(f"  X {name}: ERROR on {people}, limit={limit}: {type(e).__name__}: {e}")
    if ok:
        print(f"  OK {name}: PASS")

print()
print("ALL PASS" if all_pass else "SOME FAILURES")
