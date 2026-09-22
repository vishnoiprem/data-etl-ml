"""
Boats to Save People
====================
Each boat carries at most 2 people whose total weight <= limit.
Return the minimum number of boats needed.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/boats-to-save-people

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Each boat holds at most 2 people with total weight <= limit.
    Find the minimum number of boats to evacuate everyone."

2. OBSERVE — KEY INSIGHT:
   "Pair the HEAVIEST person with the LIGHTEST person who can fit with them.
    This is optimal because:
    - Heavy person needs their own boat if no light person can pair.
    - If lightest can't pair with heaviest, lightest needs own boat.
    - Otherwise, pairing leaves the 'most space' for the next heaviest."

3. PATTERN RECOGNITION:
   "Two-pointer technique after sorting. Lightest at left, heaviest at right.
    Pair if they fit; otherwise heaviest goes alone."

4. EDGE CASES:
   "Single person -> 1 boat.
    All weights same, all <= limit/2 -> pairs of 2 -> n/2 boats.
    All weights > limit/2 -> all need own boat -> n boats."

5. TRICKY DETAIL:
   "After sorting, we never move a person past the right pointer once
    they're 'assigned'. The two pointers converge from both ends."

6. ALGORITHM:
   "1. Sort people.
    2. left = 0, right = n-1.
    3. While left <= right:
        boats += 1
        if left == right: break (one person left)
        if people[left] + people[right] <= limit:
            left += 1  # they pair up
        right -= 1   # heaviest always gets on a boat"

7. WHY GREEDY WORKS (proof sketch):
   "Suppose heaviest goes alone. Then there's some other person on that
    boat. That person could just as easily have gone with the lightest
    person (since lightest fits if the original person fit). So pairing
    heaviest with lightest never increases boat count."

8. COMPLEXITY:
   "Time: O(n log n) for sorting, O(n) for the two-pointer scan.
    Space: O(1) extra (or O(n) for the sorted copy)."

9. CODE STRUCTURE:
   "people.sort()
    left, right = 0, len(people) - 1
    boats = 0
    while left <= right:
        boats += 1
        if left == right: break
        if people[left] + people[right] <= limit:
            left += 1
        right -= 1
    return boats"

10. MENTAL TRACE:
    people = [1, 2], limit = 3
    After sort: [1, 2], left=0, right=1
    Iteration 1: right=0, boats=1; 1+2=3<=3, left=1 -> loop ends (1 <= 0 false)
    Answer: 1 ✓

    people = [3, 2, 2, 1], limit = 3
    After sort: [1, 2, 2, 3], left=0, right=3
    Iter 1: right=2, boats=1; 1+3=4>3 -> no pair
    Iter 2: right=1, boats=2; people[0]+people[2]=1+2=3<=3 -> pair, left=1
    Iter 3: right=0, boats=3; left=1 > right=0 -> no pair
    Answer: 3 ✓ (boats: {3}, {1,2}, {2})
"""


# ==============================================================
# Solution 1: Two-pointer after sort (CANONICAL)
# ==============================================================
def rescue_boats_v1(people, limit):
    """Sort, then pair lightest + heaviest if they fit; else heaviest alone."""
    people = sorted(people)
    left, right = 0, len(people) - 1
    boats = 0
    while left <= right:
        # Heaviest (right) always gets on a boat
        right -= 1
        boats += 1
        # If lightest (left) can fit on the same boat, pair them
        if left <= right and people[left] + people[right + 1] <= limit:
            left += 1
    return boats


# ==============================================================
# Solution 2: Two-pointer without modifying input
# ==============================================================
def rescue_boats_v2(people, limit):
    """Like V1 but doesn't mutate input."""
    sorted_people = sorted(people)
    left, right = 0, len(sorted_people) - 1
    boats = 0
    while left <= right:
        right -= 1
        boats += 1
        if left <= right and sorted_people[left] + sorted_people[right + 1] <= limit:
            left += 1
    return boats


# ==============================================================
# Solution 3: Counting sort / bucket sort (O(n + limit))
# ==============================================================
def rescue_boats_v3(people, limit):
    """
    Counting sort / bucket-based approach. Since weights <= limit, use a
    freq array. For each heavy person, try to pair with the heaviest
    available person that fits below or equal to (limit - heavy).
    """
    if not people:
        return 0
    max_w = max(people)
    freq = [0] * (max_w + 1)
    for w in people:
        freq[w] += 1

    boats = 0
    heavy = max_w
    while heavy > 0:
        if freq[heavy] == 0:
            heavy -= 1
            continue
        # Take one heavy person
        freq[heavy] -= 1
        boats += 1
        # Find the heaviest partner weight that fits (light + heavy <= limit)
        # and is <= the remaining capacity
        target = limit - heavy
        if target > 0:
            light = min(target, heavy)  # can't be > heavy (would be a heavier partner)
            while light > 0 and freq[light] == 0:
                light -= 1
            if light > 0:
                freq[light] -= 1
        # If light == heavy, we already took one (above); if there's another
        # at same weight, freq[heavy] still > 0 and we'll get it next iter.
    return boats


# ==============================================================
# Solution 4: Using Counter (O(n log n) but elegant)
# ==============================================================
def rescue_boats_v4(people, limit):
    """
    Use Counter but two-pointer-like: each iteration consumes one 'heavy'
    and possibly one 'light'. We track counts separately.
    """
    from collections import Counter
    counts = Counter(people)
    weights = sorted(counts.keys())  # unique weights, ascending
    boats = 0
    left, right = 0, len(weights) - 1
    while left <= right:
        heavy = weights[right]
        # Take one heavy person
        counts[heavy] -= 1
        if counts[heavy] == 0:
            right -= 1
        boats += 1
        # Find heaviest partner weight that fits (light + heavy <= limit).
        # We want the largest light_w <= (limit - heavy).
        max_light = limit - heavy
        if left <= right and weights[left] <= max_light:
            # Binary search for largest weight <= max_light
            lo, hi = left, right
            best = left
            while lo <= hi:
                mid = (lo + hi) // 2
                if weights[mid] <= max_light:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            light = weights[best]
            counts[light] -= 1
            if counts[light] == 0:
                # Advance left pointer past all used-up weights
                while left <= right and (weights[left] not in counts):
                    left += 1
    return boats


# ==============================================================
# Solution 5: Greedy with single pass and binary search
# ==============================================================
def rescue_boats_v5(people, limit):
    """
    Sort, then for each heavy person find the lightest person who can
    pair with them using binary search.
    """
    sorted_p = sorted(people)
    boats = 0
    n = len(sorted_p)
    used = [False] * n
    for i in range(n - 1, -1, -1):
        if used[i]:
            continue
        boats += 1
        used[i] = True
        # Find lightest person who can pair
        target = limit - sorted_p[i]
        # Binary search for largest index <= target among unused
        lo, hi = 0, i
        best = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if sorted_p[mid] <= target:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        # Find the largest unused index <= best
        while best >= 0 and used[best]:
            best -= 1
        if best >= 0:
            used[best] = True
    return boats


# ==============================================================
# Solution 6: Recursive with two-pointer (educational)
# ==============================================================
def rescue_boats_v6(people, limit):
    """
    Recursive version. Pair heaviest with lightest if they fit,
    else heaviest alone.
    """
    sorted_p = sorted(people)
    n = len(sorted_p)

    def helper(lo, hi):
        if lo > hi:
            return 0
        if lo == hi:
            return 1
        # Heaviest (hi) goes on a boat. If lightest (lo) can pair, take both.
        if sorted_p[lo] + sorted_p[hi] <= limit:
            return 1 + helper(lo + 1, hi - 1)
        return 1 + helper(lo, hi - 1)

    return helper(0, n - 1)


# ==============================================================
# Solution 7: While loop with break (slightly different style)
# ==============================================================
def rescue_boats_v7(people, limit):
    """Same as V1 with explicit break conditions."""
    sorted_p = sorted(people)
    boats = 0
    left, right = 0, len(sorted_p) - 1
    while left <= right:
        right -= 1
        boats += 1
        if left <= right and sorted_p[left] + sorted_p[right + 1] <= limit:
            left += 1
    return boats


# ==============================================================
# Solution 8: Deque-based two-pointer
# ==============================================================
def rescue_boats_v8(people, limit):
    """Use deque for explicit two-pointer."""
    from collections import deque
    q = deque(sorted(people))
    boats = 0
    while q:
        heaviest = q.pop()
        boats += 1
        if q and q[0] + heaviest <= limit:
            q.popleft()
    return boats


# ==============================================================
# Solution 9: Using numpy for vectorized (O(n log n))
# ==============================================================
def rescue_boats_v9(people, limit):
    """Numpy-based implementation."""
    try:
        import numpy as np
        arr = np.sort(np.array(people))
        boats = 0
        left, right = 0, len(arr) - 1
        while left <= right:
            right -= 1
            boats += 1
            if left <= right and arr[left] + arr[right + 1] <= limit:
                left += 1
        return boats
    except ImportError:
        return rescue_boats_v1(people, limit)


# ==============================================================
# Solution 10: Mathematical — using median split
# ==============================================================
def rescue_boats_v10(people, limit):
    """
    Two-pointer with simplified structure. Decrement right and increment
    boats first (heaviest goes), then optionally pair lightest.
    """
    sorted_p = sorted(people)
    n = len(sorted_p)
    if n == 0:
        return 0
    left, right = 0, n - 1
    boats = 0
    while left <= right:
        right -= 1
        boats += 1
        if left <= right and sorted_p[left] + sorted_p[right + 1] <= limit:
            left += 1
    return boats


# ==============================================================
# Test runner
# ==============================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical two-pointer)",     rescue_boats_v1),
        ("V2 (no mutation)",               rescue_boats_v2),
        ("V3 (counting sort)",             rescue_boats_v3),
        ("V4 (Counter)",                   rescue_boats_v4),
        ("V5 (binary search)",             rescue_boats_v5),
        ("V6 (recursive)",                 rescue_boats_v6),
        ("V7 (while w/ walrus)",           rescue_boats_v7),
        ("V8 (deque)",                     rescue_boats_v8),
        ("V9 (numpy)",                     rescue_boats_v9),
        ("V10 (math-style)",               rescue_boats_v10),
    ]

    test_cases = [
        ([1, 2],                3, 1),
        ([3, 2, 2, 1],          3, 3),     # (3 alone), (1+2), (2 alone)
        ([3, 5, 3, 4],          5, 4),     # all alone
        ([1, 2, 3, 4],          5, 2),     # (1,4), (2,3)
        ([5, 1, 4, 2],          6, 2),     # (1,5), (2,4)
        ([1],                   1, 1),
        ([1, 1, 1, 1],          2, 2),     # pairs
        ([2, 2],                6, 1),
        ([2, 2],                3, 2),     # 2+2=4 > 3 -> each alone
        ([3, 3, 3],             5, 3),     # 3+3=6 > 5
        ([3, 3, 3],             6, 2),     # 3+3=6 <= 6
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
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Each boat holds at most 2 people with total weight <= limit.
2. INSIGHT:     Pair heaviest with lightest who can fit. Optimal.
3. PATTERN:     Two-pointer after sort.
4. EDGE:        Single person -> 1; all alone or all pairs.
5. TRICKY:      Heaviest always gets a boat; pair with lightest if possible.
6. ALGORITHM:   Sort + left/right pointers, decrement n, increment boats.
7. PROOF:       Exchange argument — pairing heaviest+lightest never worse.
8. COMPLEXITY:  O(n log n) time, O(1) extra space.
9. CODE:        while left <= right: boats++; if pair fits, left++; right--.
10. TRACE:      [3,2,2,1], limit=3 -> (1,2), (2,3) -> 2 boats.
""")
