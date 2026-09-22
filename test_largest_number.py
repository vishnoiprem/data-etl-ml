"""Test all 10 solutions for largest_number."""
import sys
sys.path.insert(0, '/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/educative/11_Greedy_Techniques')
import largest_number as m

sols = [
    ('V1', m.largest_number_v1),
    ('V2', m.largest_number_v2),
    ('V3', m.largest_number_v3),
    ('V4', m.largest_number_v4),
    ('V5', m.largest_number_v5),
    ('V6', m.largest_number_v6),
    ('V7', m.largest_number_v7),
    ('V8', m.largest_number_v8),
    ('V9', m.largest_number_v9),
    ('V10', m.largest_number_v10),
]
tests = [
    ([10, 2], '210'),
    ([3, 30, 34, 5, 9], '9534330'),
    ([1], '1'),
    ([10], '10'),
    ([0, 0], '0'),
    ([0, 0, 0], '0'),
    ([1, 2, 3, 4, 5], '54321'),
    ([5, 4, 3, 2, 1], '54321'),
    ([121, 12], '12121'),
    ([9, 99, 999], '999999'),
    ([830, 8308], '8308830'),
]
for name, func in sols:
    ok = True
    for arr, expected in tests:
        try:
            got = func(list(arr))
            if got != expected:
                ok = False
                print(f'  X {name}: {arr} -> {got!r} (expected {expected!r})')
        except Exception as e:
            ok = False
            print(f'  X {name}: ERROR on {arr}: {type(e).__name__}: {e}')
    if ok:
        print(f'  OK {name}: PASS')
