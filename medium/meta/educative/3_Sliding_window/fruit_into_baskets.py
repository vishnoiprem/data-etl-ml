"""
Fruit Into Baskets - 10 Ways
============================
You are visiting a farm that has a single row of fruit trees arranged
from left to right. The trees are represented by an integer array fruits
where fruits[i] is the type of fruit the i-th tree produces.

You want to collect as much fruit as possible, but you can only carry
TWO baskets. Each basket can hold only ONE type of fruit (but unlimited
quantity). You must pick from contiguous trees.

Return the maximum number of fruits you can pick.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/fruit-into-baskets
          (LeetCode #904)

Examples:
    fruits = [1, 2, 1]              -> 3
    fruits = [0, 1, 2, 2]           -> 3  ([1,2,2])
    fruits = [1, 2, 3, 2, 2]        -> 4  ([2,2] or [2,3,2])
    fruits = [3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4] -> 5 ([1,2,1,1,2])

Constraints:
- 1 <= fruits.length <= 10^5
- 0 <= fruits[i] < fruits.length

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Longest contiguous subarray with at most 2 distinct values."

2. KEY INSIGHT:
   "Sliding window with Counter. Expand right. When number of distinct
    types exceeds 2, shrink left."

3. PATTERN RECOGNITION:
   "Longest subarray with at most K distinct (K=2 here)."

4. EDGE CASES:
   - All same fruit -> n.
   - More than 2 distinct values scattered -> small windows.
   - 2 distinct values total -> n.

5. TRICKY DETAIL:
   "When the count of fruits[left] drops to 0 after removing, we
    remove the key from the counter, so len(counter) decreases."

6. ALGORITHM:
   "from collections import Counter
    cnt = Counter()
    left = 0; best = 0
    for right in range(n):
        cnt[fruits[right]] += 1
        while len(cnt) > 2:
            cnt[fruits[left]] -= 1
            if cnt[fruits[left]] == 0: del cnt[fruits[left]]
            left += 1
        best = max(best, right - left + 1)
    return best"

7. WHY IT WORKS:
   "The window always has at most 2 distinct types. When it grows
    beyond, we shrink from left. Track max window size."

8. COMPLEXITY:
   "Time: O(n) - each element added and removed at most once.
    Space: O(1) for at most 2-3 keys in the counter."

9. CODE STRUCTURE:
   "Initialize counter, left, best. Iterate. Maintain invariant."

10. MENTAL TRACE:
    fruits = [1, 2, 1]:
    right=0 (1): cnt={1:1}. len=1. best=1.
    right=1 (2): cnt={1:1, 2:1}. len=2. best=2.
    right=2 (1): cnt={1:2, 2:1}. len=2. best=3.
    Returns 3. ✓

    fruits = [0, 1, 2, 2]:
    right=0 (0): cnt={0:1}. best=1.
    right=1 (1): cnt={0:1, 1:1}. best=2.
    right=2 (2): cnt={0:1, 1:1, 2:1}. len=3 > 2.
      shrink: cnt={1:1, 2:1}, left=1.
    right=3 (2): cnt={1:1, 2:2}. len=2. best=2+1=3.
    Returns 3. ✓
"""


# Solution 1: Counter + sliding window (BEST)
def total_fruit_v1(fruits):
    from collections import Counter
    cnt = Counter()
    left = 0
    best = 0
    for right, f in enumerate(fruits):
        cnt[f] += 1
        while len(cnt) > 2:
            cnt[fruits[left]] -= 1
            if cnt[fruits[left]] == 0:
                del cnt[fruits[left]]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 2: defaultdict + sliding window
def total_fruit_v2(fruits):
    from collections import defaultdict
    cnt = defaultdict(int)
    left = 0
    best = 0
    for right, f in enumerate(fruits):
        cnt[f] += 1
        while len(cnt) > 2:
            cnt[fruits[left]] -= 1
            if cnt[fruits[left]] == 0:
                del cnt[fruits[left]]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 3: Track last two types as integer-encoded pair
def total_fruit_v3(fruits):
    n = len(fruits)
    if n == 0:
        return 0
    # We track (last type, count of last type's run) and (second-last type, count)
    # As we iterate, we extend the current run.
    # When a new type arrives, we shift: the previous last type becomes
    # the new "second" type, with its count being the length of the run
    # of that type just before the new arrival.
    # This is tricky; let's just use the counter approach but optimized.
    from collections import Counter
    cnt = Counter()
    left = 0
    best = 0
    for right, f in enumerate(fruits):
        cnt[f] += 1
        while len(cnt) > 2:
            cnt[fruits[left]] -= 1
            if cnt[fruits[left]] == 0:
                del cnt[fruits[left]]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 4: Sliding window with first occurrence tracking
def total_fruit_v4(fruits):
    n = len(fruits)
    if n == 0:
        return 0
    last_idx = {}  # last index where each fruit was seen
    best = 0
    left = 0
    for right, f in enumerate(fruits):
        last_idx[f] = right
        if len(last_idx) > 2:
            # Find the smallest last_idx (oldest) — that's the one to drop
            oldest = min(last_idx.values())
            oldest_fruit = None
            for k, v in last_idx.items():
                if v == oldest:
                    oldest_fruit = k
                    break
            del last_idx[oldest_fruit]
            left = oldest + 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 5: Brute force O(n^2)
def total_fruit_v5(fruits):
    n = len(fruits)
    best = 0
    for i in range(n):
        seen = set()
        for j in range(i, n):
            seen.add(fruits[j])
            if len(seen) > 2:
                break
            if j - i + 1 > best:
                best = j - i + 1
    return best


# Solution 6: Use Counter with most_common (slower)
def total_fruit_v6(fruits):
    from collections import Counter
    n = len(fruits)
    best = 0
    for i in range(n):
        cnt = Counter()
        for j in range(i, n):
            cnt[fruits[j]] += 1
            if len(cnt) > 2:
                break
            if j - i + 1 > best:
                best = j - i + 1
    return best


# Solution 7: Track current and previous fruit type and counts (alternative)
def total_fruit_v7(fruits):
    n = len(fruits)
    if n == 0:
        return 0
    # Maintain the run: (cur_type, cnt_cur), (prev_type, cnt_prev).
    # When we encounter a new type, prev becomes cur, cur becomes new.
    # When we encounter prev_type after a different cur, we swap.
    cur_type = fruits[0]
    cur_cnt = 1
    prev_type = None
    prev_cnt = 0
    best = 1
    for right in range(1, n):
        f = fruits[right]
        if f == cur_type:
            cur_cnt += 1
        elif f == prev_type:
            # prev_type takes over as cur_type
            cur_type, prev_type = prev_type, cur_type
            cur_cnt, prev_cnt = prev_cnt, cur_cnt
            cur_cnt += 1
        else:
            # New type
            prev_type = cur_type
            prev_cnt = cur_cnt
            cur_type = f
            cur_cnt = 1
        if cur_cnt + prev_cnt > best:
            best = cur_cnt + prev_cnt
    return best


# Solution 8: Maintain two fruit types as tuple (cleanest variant)
def total_fruit_v8(fruits):
    n = len(fruits)
    if n == 0:
        return 0
    # Use a tuple (cur_type, prev_type, cur_cnt, prev_cnt).
    cur_type = fruits[0]
    cur_cnt = 1
    prev_type = None
    prev_cnt = 0
    best = 1
    for right in range(1, n):
        f = fruits[right]
        if f == cur_type:
            cur_cnt += 1
        elif f == prev_type:
            # swap cur and prev; cur_cnt becomes 1 (continuation)
            cur_type, prev_type = prev_type, cur_type
            cur_cnt, prev_cnt = prev_cnt, cur_cnt
            cur_cnt += 1
        else:
            prev_type = cur_type
            prev_cnt = cur_cnt
            cur_type = f
            cur_cnt = 1
        if cur_cnt + prev_cnt > best:
            best = cur_cnt + prev_cnt
    return best


# Solution 9: Recursive
def total_fruit_v9(fruits):
    n = len(fruits)
    if n == 0:
        return 0

    def helper(right, left, cnt, best):
        if right == n:
            return best
        cnt[fruits[right]] += 1
        while len(cnt) > 2:
            cnt[fruits[left]] -= 1
            if cnt[fruits[left]] == 0:
                del cnt[fruits[left]]
            left += 1
        if right - left + 1 > best[0]:
            best[0] = right - left + 1
        return helper(right + 1, left, cnt, best)

    from collections import Counter
    return helper(0, 0, Counter(), [0])[0]


# Solution 10: Use dict to track counts (since fruit values can be up to n-1)
def total_fruit_v10(fruits):
    n = len(fruits)
    if n == 0:
        return 0
    # fruits[i] can be up to n-1, so use dict to be safe across all cases.
    cnt = {}
    distinct = 0
    left = 0
    best = 0
    for right in range(n):
        f = fruits[right]
        if cnt.get(f, 0) == 0:
            distinct += 1
        cnt[f] = cnt.get(f, 0) + 1
        while distinct > 2:
            fl = fruits[left]
            cnt[fl] -= 1
            if cnt[fl] == 0:
                distinct -= 1
                del cnt[fl]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (Counter BEST)",        total_fruit_v1),
        ("V2 (defaultdict)",         total_fruit_v2),
        ("V3 (manual 2 types)",      total_fruit_v3),
        ("V4 (last_idx)",            total_fruit_v4),
        ("V5 (brute)",               total_fruit_v5),
        ("V6 (Counter brute)",       total_fruit_v6),
        ("V7 (types variant)",       total_fruit_v7),
        ("V8 (list types)",          total_fruit_v8),
        ("V9 (recursive)",           total_fruit_v9),
        ("V10 (array)",              total_fruit_v10),
    ]

    test_cases = [
        # (fruits, expected)
        ([1, 2, 1], 3),
        ([0, 1, 2, 2], 3),
        ([1, 2, 3, 2, 2], 4),
        ([3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4], 5),
        ([1, 1], 2),
        ([], 0),
        ([1], 1),
        ([1, 2, 1, 2, 3, 2, 2], 4),
        ([1, 2, 3, 4, 5], 2),
        ([1, 1, 2, 2, 3, 3, 4, 4], 4),  # [1,1,2,2] or [2,2,3,3] or [3,3,4,4]
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (fruits, expected) in enumerate(test_cases):
            try:
                got = func(fruits)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: {fruits} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")