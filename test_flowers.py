import sys
sys.path.insert(0, '/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/educative/11_Greedy_Techniques')
import can_place_flowers as m

solutions = [
    ('V1', m.can_place_flowers_v1),
    ('V2', m.can_place_flowers_v2),
    ('V3', m.can_place_flowers_v3),
    ('V4', m.can_place_flowers_v4),
    ('V5', m.can_place_flowers_v5),
    ('V6', m.can_place_flowers_v6),
    ('V7', m.can_place_flowers_v7),
    ('V8', m.can_place_flowers_v8),
    ('V9', m.can_place_flowers_v9),
    ('V10', m.can_place_flowers_v10),
]
test_cases = [
    ([1, 0, 0, 0, 1],        1, True),
    ([1, 0, 0, 0, 1],        2, False),
    ([1, 0, 0, 0, 1, 0, 0],  2, True),
    ([0, 0, 1, 0, 0],        1, True),
    ([0, 0, 1, 0, 0],        2, True),   # plant at 0 and 4
    ([0],                    1, True),
    ([1],                    0, True),
    ([1],                    1, False),
    ([0, 0, 0, 0, 0],        3, True),
    ([1, 0, 1, 0, 1, 0, 1],  0, True),
    ([1, 0, 1, 0, 1, 0, 1],  1, False),
]
for name, func in solutions:
    ok = True
    for bed, n, expected in test_cases:
        try:
            got = func(list(bed), n)
            if got != expected:
                ok = False
                print(f'  X {name}: {bed}, n={n} -> {got} (expected {expected})')
        except Exception as e:
            ok = False
            print(f'  X {name}: ERROR on {bed}, n={n}: {type(e).__name__}: {e}')
    if ok:
        print(f'  OK {name}: PASS')
