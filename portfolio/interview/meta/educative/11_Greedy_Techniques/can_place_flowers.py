"""
Can Place Flowers
=================
Given a flowerbed (0 = empty, 1 = planted) and an integer n, determine
if n new flowers can be planted without adjacent flowers.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/can-place-flowers

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "I have a flowerbed with empty (0) and planted (1) plots. I need
    to plant n more flowers. Constraint: no two adjacent plots can
    both have flowers. Can I do it?"

2. OBSERVE — KEY INSIGHT:
   "Greedy: plant at the LEFTMOST valid empty plot first. Each plant
    uses up the maximum empty space, so left-to-right placement is
    optimal (proven by exchange argument)."

3. PATTERN RECOGNITION:
   "This is a greedy / one-pass scan problem. Track available
    consecutive empty plots and decide where to plant."

4. EDGE CASES:
   "What if n == 0? -> trivially True.
    What about the boundaries? Plot 0 has no left neighbor;
    Plot len-1 has no right neighbor. So they're 'easier' to plant."

5. TRICKY DETAIL:
   "A plot i can be planted if BOTH i-1 and i+1 are empty (or out of
    bounds). So check flowerbed[i-1] (or treat as 0) and flowerbed[i+1]."

6. ALGORITHM (single pass):
   "For each plot i:
      if flowerbed[i] == 0 AND left empty AND right empty:
        plant here (set to 1, decrement n)
      if n == 0: return True
    return n == 0 at end"

7. WHY GREEDY WORKS:
   "Planting leftmost doesn't reduce ability to plant later. In fact,
    it's optimal because planting leftmost maximizes the remaining
    'free space' on the right (where the boundary is also easier)."

8. COMPLEXITY:
   "Time: O(len(flowerbed)) — one pass.
    Space: O(1) — in-place modifications (or copy if not allowed)."

9. CODE STRUCTURE:
   "for i in range(len(flowerbed)):
        prev = flowerbed[i-1] if i > 0 else 0
        next = flowerbed[i+1] if i+1 < len(flowerbed) else 0
        if flowerbed[i] == 0 and prev == 0 and next == 0:
            flowerbed[i] = 1
            n -= 1
            if n == 0: return True
    return n <= 0"

10. MENTAL TRACE:
    [1,0,0,0,1], n=1
    i=0: flowerbed[0]=1, skip
    i=1: prev=1, skip
    i=2: prev=0, next=0, flowerbed[2]=0 -> plant! flowerbed=[1,0,1,0,1], n=0, True ✓
"""


# ==============================================================
# Solution 1: In-place greedy single-pass (CANONICAL)
# ==============================================================
def can_place_flowers_v1(flowerbed, n):
    """
    Single left-to-right pass. Plant at each valid plot.
    Modify flowerbed in place.
    """
    if n <= 0:
        return True
    length = len(flowerbed)
    for i in range(length):
        if flowerbed[i] == 0:
            prev = flowerbed[i - 1] if i > 0 else 0
            nxt = flowerbed[i + 1] if i + 1 < length else 0
            if prev == 0 and nxt == 0:
                flowerbed[i] = 1
                n -= 1
                if n == 0:
                    return True
    return n <= 0


# ==============================================================
# Solution 2: Non-mutating single pass (returns bool, copies internally)
# ==============================================================
def can_place_flowers_v2(flowerbed, n):
    """
    Like V1 but doesn't mutate the input.
    """
    if n <= 0:
        return True
    bed = list(flowerbed)
    length = len(bed)
    for i in range(length):
        if bed[i] == 0:
            prev = bed[i - 1] if i > 0 else 0
            nxt = bed[i + 1] if i + 1 < length else 0
            if prev == 0 and nxt == 0:
                bed[i] = 1
                n -= 1
                if n == 0:
                    return True
    return n <= 0


# ==============================================================
# Solution 3: With sentinel padding (cleaner boundary check)
# ==============================================================
def can_place_flowers_v3(flowerbed, n):
    """
    Pad flowerbed with zeros at both ends so we don't need boundary checks.
    """
    if n <= 0:
        return True
    bed = [0] + list(flowerbed) + [0]
    for i in range(1, len(bed) - 1):
        if bed[i] == 0 and bed[i - 1] == 0 and bed[i + 1] == 0:
            bed[i] = 1
            n -= 1
            if n == 0:
                return True
    return n <= 0


# ==============================================================
# Solution 4: Skip-over-planted greedy (jump i by 2 after planting)
# ==============================================================
def can_place_flowers_v4(flowerbed, n):
    """
    After planting at i, the next valid i is i+2 (since i+1 is now blocked).
    """
    if n <= 0:
        return True
    length = len(flowerbed)
    i = 0
    planted = 0
    while i < length:
        if flowerbed[i] == 0:
            prev = flowerbed[i - 1] if i > 0 else 0
            nxt = flowerbed[i + 1] if i + 1 < length else 0
            if prev == 0 and nxt == 0:
                planted += 1
                if planted >= n:
                    return True
                i += 2  # next valid position is i+2
                continue
        i += 1
    return planted >= n


# ==============================================================
# Solution 5: Count max possible flowers formula
# ==============================================================
def can_place_flowers_v5(flowerbed, n):
    """
    Formula: max flowers that can be planted =
        sum over consecutive empty segments:
            (segment_length + 1) // 2  -- if segment is at edge
            (segment_length) // 2      -- if segment is internal
    Then check if max >= n.
    """
    if n <= 0:
        return True
    max_plantable = 0
    length = len(flowerbed)
    i = 0
    while i < length:
        if flowerbed[i] == 1:
            i += 1
            continue
        # Count consecutive zeros starting at i
        start = i
        while i < length and flowerbed[i] == 0:
            i += 1
        seg_len = i - start
        # Is this segment at the edges?
        if start == 0 and i == length:
            max_plantable += (seg_len + 1) // 2
        elif start == 0 or i == length:
            max_plantable += seg_len // 2
            if seg_len % 2 == 1:
                max_plantable += 1
        else:
            max_plantable += (seg_len - 1) // 2
    return max_plantable >= n


# ==============================================================
# Solution 6: Recursive greedy
# ==============================================================
def can_place_flowers_v6(flowerbed, n):
    """
    Recursive: try to plant at the first valid spot, recurse on the rest.
    """
    if n <= 0:
        return True
    bed = list(flowerbed)
    length = len(bed)

    def helper(i, remaining):
        if remaining <= 0:
            return True
        if i >= length:
            return False
        prev = bed[i - 1] if i > 0 else 0
        nxt = bed[i + 1] if i + 1 < length else 0
        if bed[i] == 0 and prev == 0 and nxt == 0:
            bed[i] = 1
            return helper(i + 2, remaining - 1)
        return helper(i + 1, remaining)

    return helper(0, n)


# ==============================================================
# Solution 7: Memoized recursive
# ==============================================================
def can_place_flowers_v7(flowerbed, n):
    """
    Memoize (i, n) to avoid redundant recursion.
    """
    if n <= 0:
        return True
    bed = list(flowerbed)
    length = len(bed)
    memo = {}

    def helper(i, remaining):
        if remaining <= 0:
            return True
        if i >= length:
            return False
        key = (i, remaining)
        if key in memo:
            return memo[key]
        prev = bed[i - 1] if i > 0 else 0
        nxt = bed[i + 1] if i + 1 < length else 0
        result = False
        if bed[i] == 0 and prev == 0 and nxt == 0:
            bed[i] = 1
            result = helper(i + 2, remaining - 1)
            bed[i] = 0  # backtrack
        if not result:
            result = helper(i + 1, remaining)
        memo[key] = result
        return result

    return helper(0, n)


# ==============================================================
# Solution 8: Using iterators / generator
# ==============================================================
def can_place_flowers_v8(flowerbed, n):
    """
    Use a generator-like style with enumerate and explicit state.
    """
    if n <= 0:
        return True
    bed = list(flowerbed)
    planted = 0
    for i, val in enumerate(bed):
        if val != 0:
            continue
        prev = bed[i - 1] if i > 0 else 0
        nxt = bed[i + 1] if i + 1 < len(bed) else 0
        if prev == 0 and nxt == 0:
            bed[i] = 1
            planted += 1
            if planted >= n:
                return True
    return planted >= n


# ==============================================================
# Solution 9: While-loop with i increment by 1 (alternative)
# ==============================================================
def can_place_flowers_v9(flowerbed, n):
    """
    Iterate i from 0 to len. Increment by 1 always; the check naturally
    handles planted plots.
    """
    if n <= 0:
        return True
    bed = list(flowerbed)
    length = len(bed)
    i = 0
    while i < length:
        if bed[i] == 1:
            i += 1
            continue
        prev_empty = (i == 0) or (bed[i - 1] == 0)
        nxt_empty = (i == length - 1) or (bed[i + 1] == 0)
        if prev_empty and nxt_empty:
            bed[i] = 1
            n -= 1
            if n <= 0:
                return True
        i += 1
    return n <= 0


# ==============================================================
# Solution 10: One-liner with all() for next plot check
# ==============================================================
def can_place_flowers_v10(flowerbed, n):
    """
    Compact solution using all() to check neighborhood.
    """
    if n <= 0:
        return True
    bed = list(flowerbed)
    length = len(bed)
    for i in range(length):
        if bed[i] != 0:
            continue
        if all(bed[j] == 0 for j in [i - 1, i + 1] if 0 <= j < length):
            bed[i] = 1
            n -= 1
            if n <= 0:
                return True
    return n <= 0


# ==============================================================
# Test runner
# ==============================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (in-place greedy)",        can_place_flowers_v1),
        ("V2 (non-mutating)",           can_place_flowers_v2),
        ("V3 (sentinel padding)",       can_place_flowers_v3),
        ("V4 (skip by 2)",              can_place_flowers_v4),
        ("V5 (formula-based)",          can_place_flowers_v5),
        ("V6 (recursive greedy)",       can_place_flowers_v6),
        ("V7 (memoized recursion)",     can_place_flowers_v7),
        ("V8 (enumerate)",              can_place_flowers_v8),
        ("V9 (while loop)",             can_place_flowers_v9),
        ("V10 (all() check)",           can_place_flowers_v10),
    ]

    test_cases = [
        ([1, 0, 0, 0, 1],        1, True),   # plant at index 2
        ([1, 0, 0, 0, 1],        2, False),  # only one slot
        ([1, 0, 0, 0, 1, 0, 0],  2, True),   # plant at 2 and 5
        ([0, 0, 1, 0, 0],        1, True),
        ([0, 0, 1, 0, 0],        2, True),   # plant at 0 and 4
        ([0],                    1, True),   # single empty plot
        ([1],                    0, True),
        ([1],                    1, False),
        ([0, 0, 0, 0, 0],        3, True),   # 0,2,4 or 0,3
        ([1, 0, 1, 0, 1, 0, 1],  0, True),
        ([1, 0, 1, 0, 1, 0, 1],  1, False),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for bed, n, expected in test_cases:
            try:
                got = func(list(bed), n)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name}: bed={bed}, n={n} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name}: ERROR on bed={bed}, n={n}: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Can I plant n flowers without adjacent flowers?
2. INSIGHT:     Greedy — plant at leftmost valid spot.
3. PATTERN:     One-pass with neighborhood check.
4. EDGE:        n=0 -> True; boundaries have no neighbor.
5. TRICKY:      Boundaries! Plot 0 has no left; plot N-1 has no right.
6. ALGORITHM:   Scan, plant at valid plots, decrement n.
7. PROOF:       Leftmost planting maximizes remaining free space (exchange arg).
8. COMPLEXITY:  O(n) time, O(1) space (in-place).
9. CODE:        prev = bed[i-1] if i > 0 else 0; same for next.
10. TRACE:      [1,0,0,0,1],n=1 -> plant at 2 -> [1,0,1,0,1] -> True.
""")
