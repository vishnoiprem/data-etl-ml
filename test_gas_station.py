"""Test runner for gas_station.py"""
import sys
sys.path.insert(0, '/Users/pvishnoi/PycharmProjects/data-etl-ml/medium/meta/educative/11_Greedy_Techniques')
import gas_station as m

solutions = [
    ("V1", m.gas_station_v1),
    ("V2", m.gas_station_v2),
    ("V3", m.gas_station_v3),
    ("V4", m.gas_station_v4),
    ("V5", m.gas_station_v5),
    ("V6", m.gas_station_v6),
    ("V7", m.gas_station_v7),
    ("V8", m.gas_station_v8),
    ("V9", m.gas_station_v9),
    ("V10", m.gas_station_v10),
]

test_cases = [
    ("basic",       [1, 5, 3, 3, 4],     [4, 4, 1, 1, 1],       1),
    ("impossible", [2, 3, 4],           [3, 4, 3],             -1),
    ("single ok",  [2],                 [2],                   0),
    ("single fail", [1],                [2],                  -1),
    ("two equal",  [1, 1],              [1, 1],                0),
    ("two deficit", [0, 5, 2],          [1, 3, 4],             1),
    ("cyclic-1",   [5, 1, 2, 3, 4],     [4, 4, 1, 1, 1],       0),
    ("long diff",  [3, 1, 1],           [2, 2, 2],             -1),
    ("long ok",    [4, 1, 1, 2],        [2, 2, 2, 2],          0),
    ("all zeros",  [0, 0, 0],           [0, 0, 0],             0),
    ("unique big", [2, 3, 4, 5, 6, 1],  [3, 4, 5, 6, 7, 0],    -1),
]

all_pass = True
for name, func in solutions:
    ok = True
    for case_name, g, c, expected in test_cases:
        try:
            got = func(list(g), list(c))
            if got != expected:
                ok = False
                all_pass = False
                print(f"  X {name} [{case_name}]: gas={g}, cost={c} -> {got} (expected {expected})")
        except Exception as e:
            ok = False
            all_pass = False
            print(f"  X {name} [{case_name}]: ERROR: {type(e).__name__}: {e}")
    if ok:
        print(f"  OK {name}: PASS")

print()
print("ALL PASS" if all_pass else "SOME FAILURES")
