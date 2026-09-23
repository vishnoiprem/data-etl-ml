"""
Combination Sum
Medium | 30 min

Given an array of distinct integers nums and integer target, return all
unique combinations of nums where chosen numbers sum to target. The
same number may be chosen an unlimited number of times.

Two combinations are unique if the frequency of at least one chosen
number is different.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/combination-sum

Examples:
    nums=[2,3,6,7], target=7 -> [[2,2,3],[7]]
    nums=[2,3,5], target=8   -> [[2,2,2,2],[2,3,3],[3,5]]
    nums=[2], target=1       -> []

Constraints:
- 1 <= nums.length <= 30
- 2 <= nums[i] <= 40
- 1 <= target <= 40
- All nums distinct.

KEY INSIGHT:
Backtracking with index progression.
- Sort nums.
- DFS(remain, start): try nums[i] for i in [start, n).
- After picking nums[i], recurse with i (not i+1) since reuse allowed.
- When remain == 0, save path.
- Pruning: skip nums[i] > remain.
"""


# =============================================================================
# WAY 1: Backtracking (BEST - Memorize!)
# =============================================================================
def combination_sum_1(nums, target):
    """Standard backtracking."""
    nums = sorted(nums)
    result = []

    def dfs(remain, start, path):
        if remain == 0:
            result.append(path[:])
            return
        if remain < 0:
            return
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            path.append(nums[i])
            dfs(remain - nums[i], i, path)
            path.pop()

    dfs(target, 0, [])
    return result


# =============================================================================
# WAY 2: Backtracking without sort
# =============================================================================
def combination_sum_2(nums, target):
    """No sort, but check nums[i] > remain to prune."""
    result = []
    nums_set = set(nums)

    def dfs(remain, start, path):
        if remain == 0:
            result.append(path[:])
            return
        for i in range(start, len(nums)):
            if nums[i] > remain:
                continue
            path.append(nums[i])
            dfs(remain - nums[i], i, path)
            path.pop()

    dfs(target, 0, [])
    return result


# =============================================================================
# WAY 3: Iterative DP building combinations
# =============================================================================
def combination_sum_3(nums, target):
    """DP: dp[i] = list of combinations summing to i."""
    dp = [[] for _ in range(target + 1)]
    dp[0] = [[]]
    nums = sorted(nums)
    for i in range(1, target + 1):
        for n in nums:
            if n > i:
                break
            for combo in dp[i - n]:
                # Avoid duplicates: only add combos that start with >= n
                if not combo or combo[-1] <= n:
                    dp[i].append(combo + [n])
    return dp[target]


# =============================================================================
# WAY 4: BFS / iterative
# =============================================================================
def combination_sum_4(nums, target):
    """BFS with state (current_sum, start_idx, combo). Uses start
    to enforce non-decreasing combos (deduplication)."""
    from collections import deque
    nums = sorted(nums)
    queue = deque([(0, 0, [])])
    result = []
    while queue:
        cur_sum, start, combo = queue.popleft()
        for i in range(start, len(nums)):
            n = nums[i]
            new_sum = cur_sum + n
            if new_sum > target:
                break
            new_combo = combo + [n]
            if new_sum == target:
                result.append(new_combo)
            else:
                queue.append((new_sum, i, new_combo))
    return result


# =============================================================================
# WAY 5: Recursive with explicit memo
# =============================================================================
def combination_sum_5(nums, target):
    """DFS with memoization on (start, remain)."""
    nums = sorted(nums)
    memo = {}

    def dfs(start, remain):
        if (start, remain) in memo:
            return memo[(start, remain)]
        if remain == 0:
            return [[]]
        result = []
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            sub = dfs(i, remain - nums[i])
            for combo in sub:
                result.append([nums[i]] + combo)
        memo[(start, remain)] = result
        return result

    return dfs(0, target)


# =============================================================================
# WAY 6: Class OOP
# =============================================================================
class CombinationFinder:
    def __init__(self, nums, target):
        self.nums = sorted(nums)
        self.target = target
        self.result = []

    def solve(self):
        self._dfs(self.target, 0, [])
        return self.result

    def _dfs(self, remain, start, path):
        if remain == 0:
            self.result.append(path[:])
            return
        if remain < 0:
            return
        for i in range(start, len(self.nums)):
            if self.nums[i] > remain:
                break
            path.append(self.nums[i])
            self._dfs(remain - self.nums[i], i, path)
            path.pop()


def combination_sum_6(nums, target):
    return CombinationFinder(nums, target).solve()


# =============================================================================
# WAY 7: Backtrack without for-loop (recursive combinations)
# =============================================================================
def combination_sum_7(nums, target):
    """Recursive choice: pick nums[0] or skip to next."""
    nums = sorted(nums)
    result = []

    def dfs(remain, idx, path):
        if remain == 0:
            result.append(path[:])
            return
        if idx >= len(nums) or remain < 0:
            return
        # Pick nums[idx] (with reuse, stay at idx)
        path.append(nums[idx])
        dfs(remain - nums[idx], idx, path)
        path.pop()
        # Skip nums[idx]
        dfs(remain, idx + 1, path)

    dfs(target, 0, [])
    return result


# =============================================================================
# WAY 8: Tail recursion style
# =============================================================================
def combination_sum_8(nums, target):
    nums = sorted(nums)
    result = []

    def dfs(remain, start, path):
        if remain == 0:
            result.append(path[:])
            return
        if start >= len(nums):
            return
        n = nums[start]
        # Count how many times we can pick n
        cnt = 0
        cur_remain = remain
        while cur_remain >= 0:
            path.extend([n] * cnt)
            dfs(cur_remain, start + 1, path)
            # Undo the additions
            if cnt > 0:
                del path[-cnt:]
            cur_remain -= n
            cnt += 1
            if n == 0:
                break  # avoid infinite loop

    dfs(target, 0, [])
    return result


# =============================================================================
# WAY 9: Generator-based
# =============================================================================
def combination_sum_9(nums, target):
    """Generator yielding combinations, then collect."""
    nums = sorted(nums)

    def gen(remain, start, path):
        if remain == 0:
            yield path[:]
            return
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            yield from gen(remain - nums[i], i, path + [nums[i]])

    return list(gen(target, 0, []))


# =============================================================================
# WAY 10: 2D DP with check
# =============================================================================
def combination_sum_10(nums, target):
    """DP table: dp[i] = list of lists summing to i."""
    nums = sorted(nums)
    dp = [[] for _ in range(target + 1)]
    dp[0] = [[]]
    for n in nums:
        for i in range(n, target + 1):
            for combo in dp[i - n]:
                # Only add combos where last element <= n (to avoid dups)
                if not combo or combo[-1] <= n:
                    dp[i].append(combo + [n])
    return dp[target]


# =============================================================================
# WAY 11: Itertools-style with filters
# =============================================================================
def combination_sum_11(nums, target):
    """Build via combinations-with-replacement."""
    from itertools import combinations_with_replacement
    nums = sorted(nums)
    result = []
    # Max count = target // min(nums)
    max_count = target // nums[0] if nums else 0
    for k in range(1, max_count + 1):
        for combo in combinations_with_replacement(nums, k):
            if sum(combo) == target:
                result.append(list(combo))
    return result


# =============================================================================
# WAY 12: DP without last-check (allow all, then dedupe)
# =============================================================================
def combination_sum_12(nums, target):
    """Build all combinations, dedupe at end."""
    nums = sorted(nums)
    dp = [[] for _ in range(target + 1)]
    dp[0] = [[]]
    for n in nums:
        for i in range(n, target + 1):
            for combo in dp[i - n]:
                dp[i].append(combo + [n])
    # Dedupe
    unique = set()
    for combo in dp[target]:
        unique.add(tuple(combo))
    return [list(c) for c in unique]


# =============================================================================
# WAY 13: Brute force combinations with repetition
# =============================================================================
def combination_sum_13(nums, target):
    """Try all combinations with repetition, filter by sum."""
    from itertools import combinations_with_replacement
    nums = sorted(nums)
    result = []
    if not nums:
        return result
    max_k = target // nums[0]
    for k in range(1, max_k + 1):
        for combo in combinations_with_replacement(nums, k):
            if sum(combo) == target:
                result.append(list(combo))
    return result


# =============================================================================
# WAY 14: Backtrack with visited set to avoid dups
# =============================================================================
def combination_sum_14(nums, target):
    """Backtrack using set for dedup at each level."""
    nums = sorted(nums)
    result = []

    def dfs(remain, start, path):
        if remain == 0:
            result.append(path[:])
            return
        seen = set()
        for i in range(start, len(nums)):
            if nums[i] > remain or nums[i] in seen:
                continue
            seen.add(nums[i])
            path.append(nums[i])
            dfs(remain - nums[i], i, path)  # i, not i+1, since reuse allowed
            path.pop()

    dfs(target, 0, [])
    return result


# =============================================================================
# WAY 15: Backtrack with start for uniqueness
# =============================================================================
def combination_sum_15(nums, target):
    """Cleaner backtrack with explicit start."""
    nums = sorted(nums)
    result = []

    def dfs(remain, idx, path):
        if remain == 0:
            result.append(path[:])
            return
        for i in range(idx, len(nums)):
            if nums[i] > remain:
                break
            path.append(nums[i])
            dfs(remain - nums[i], i, path)
            path.pop()

    dfs(target, 0, [])
    return result


# =============================================================================
# WAY 16: Memoization (Pythonic dict)
# =============================================================================
def combination_sum_16(nums, target):
    """Memoize results of dfs(start, remain)."""
    nums = sorted(nums)
    memo = {}

    def dfs(start, remain):
        key = (start, remain)
        if key in memo:
            return memo[key]
        if remain == 0:
            return [[]]
        result = []
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            for sub in dfs(i, remain - nums[i]):
                result.append([nums[i]] + sub)
        memo[key] = result
        return result

    return dfs(0, target)


# =============================================================================
# WAY 17: Numpy DP for counting then reconstruct
# =============================================================================
def combination_sum_17(nums, target):
    """Use DP for counting, then DFS to enumerate."""
    nums = sorted(nums)
    # dp[i] = list of combos summing to i
    dp = [[] for _ in range(target + 1)]
    dp[0] = [[]]
    for i in range(1, target + 1):
        for n in nums:
            if n > i:
                break
            for combo in dp[i - n]:
                if not combo or combo[-1] <= n:
                    dp[i].append(combo + [n])
    return dp[target]


# =============================================================================
# WAY 18: Iterative stack-based DFS
# =============================================================================
def combination_sum_18(nums, target):
    """Stack-based DFS (no recursion)."""
    nums = sorted(nums)
    result = []
    stack = [(target, 0, [])]
    while stack:
        remain, start, path = stack.pop()
        if remain == 0:
            result.append(path[:])
            continue
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            stack.append((remain - nums[i], i, path + [nums[i]]))
    return result


# =============================================================================
# WAY 19: Backtrack with iterative deepening
# =============================================================================
def combination_sum_19(nums, target):
    """Iterative deepening by length, with deduplication at end."""
    nums = sorted(nums)
    seen = set()
    result = []

    def dfs(remain, start, path, depth):
        if remain == 0:
            key = tuple(path)
            if key not in seen:
                seen.add(key)
                result.append(path[:])
            return
        if depth == 0:
            return
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            path.append(nums[i])
            dfs(remain - nums[i], i, path, depth - 1)
            path.pop()

    max_depth = target // nums[0] if nums else 0
    for d in range(1, max_depth + 1):
        dfs(target, 0, [], d)
    return result


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def combination_sum_20(nums, target):
    """
    THE ONE TO MEMORIZE.

    Backtracking:
    1. Sort nums (for early termination).
    2. dfs(remain, start, path):
       - If remain == 0: save path.
       - For i in [start, n):
           - If nums[i] > remain: break.
           - Pick nums[i], recurse with i (reuse allowed).
           - Undo pick.

    Time:  O(N^(T/M)) where N=len(nums), T=target, M=min(nums).
    Space: O(T/M) for recursion depth.
    """
    nums = sorted(nums)
    result = []

    def dfs(remain, start, path):
        if remain == 0:
            result.append(path[:])
            return
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            path.append(nums[i])
            dfs(remain - nums[i], i, path)
            path.pop()

    dfs(target, 0, [])
    return result


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Find all unique combinations of nums that sum to target. Each number
can be used unlimited times."

Key Insight:
"Backtracking with index progression.
1. Sort nums (enables early termination when nums[i] > remain).
2. dfs(remain, start, path):
   - If remain == 0: save path.
   - For i in range(start, len(nums)):
       - If nums[i] > remain: break (sorted, no need to continue).
       - Pick nums[i], recurse with i (NOT i+1, since reuse allowed).
       - Undo (backtrack).
3. The 'start' ensures we don't generate duplicate combinations in
   different orders (e.g., [2,3] and [3,2])."

Algorithm:
1. Sort nums.
2. Backtrack from start=0 with full remaining.
3. For each candidate >= start:
   - If nums[i] > remain: break.
   - Add to path, recurse with same i (reuse).
   - Pop and continue.
4. Return collected combos.

Edge Cases:
- Empty nums (but constraint says len >= 1).
- target < min(nums): return [].
- Single element, single match.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Backtrack| O(N^T/M)| O(T/M)|
| DP build | O(N*T) | O(T*k) |
| BFS      | O(...) | O(...) |
+----------+--------+--------+
where T=target, M=min(nums), k=avg combos.

THE TRICK:
- start index prevents reordering duplicates.
- After picking nums[i], recurse with i (not i+1) since reuse allowed.
- Sort enables early termination.

ALTERNATE: DP — build combos for each sum incrementally.

RELATED:
- Combination Sum II (LC 40): no reuse, has duplicates.
- Combination Sum III (LC 216): k numbers.
- Combination Sum IV (LC 377): count permutations.
- Coin Change (LC 322): min coins.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Backtrack (BEST)", combination_sum_1),
        ("Way 2: No sort", combination_sum_2),
        ("Way 3: Iterative DP", combination_sum_3),
        ("Way 4: BFS", combination_sum_4),
        ("Way 5: Memoized DFS", combination_sum_5),
        ("Way 6: Class OOP", combination_sum_6),
        ("Way 7: Recursive choice", combination_sum_7),
        ("Way 8: Tail recursion", combination_sum_8),
        ("Way 9: Generator", combination_sum_9),
        ("Way 10: 2D DP check", combination_sum_10),
        ("Way 11: Itertools", combination_sum_11),
        ("Way 12: DP + dedupe", combination_sum_12),
        ("Way 13: Brute combos", combination_sum_13),
        ("Way 14: Backtrack seen", combination_sum_14),
        ("Way 15: Backtrack start", combination_sum_15),
        ("Way 16: Memo dict", combination_sum_16),
        ("Way 17: Numpy DP", combination_sum_17),
        ("Way 18: Stack DFS", combination_sum_18),
        ("Way 19: Iter deepening", combination_sum_19),
        ("Way 20: Final cleanest", combination_sum_20),
    ]

    # Each test case: (nums, target, expected_count, expected_combos)
    # We compare by sorted tuple of combos for canonical form.
    def normalize(result):
        return sorted(tuple(sorted(c)) for c in result)

    test_cases = [
        ([2, 3, 6, 7], 7, [tuple([2, 2, 3]), tuple([7])]),
        ([2, 3, 5], 8, [tuple([2, 2, 2, 2]), tuple([2, 3, 3]), tuple([3, 5])]),
        ([2], 1, []),
        ([1], 1, [tuple([1])]),
        ([1], 2, [tuple([1, 1])]),
        ([2, 5, 3], 9, [tuple([2, 2, 2, 3]), tuple([2, 2, 5]), tuple([3, 3, 3])]),
        ([3, 1, 2], 4, [tuple([1, 1, 1, 1]), tuple([1, 1, 2]), tuple([1, 3]), tuple([2, 2])]),
        ([2, 3, 5], 1, []),
        ([3, 5, 7], 15, [tuple([3, 3, 3, 3, 3]), tuple([3, 5, 7]), tuple([5, 5, 5])]),
    ]

    print("=" * 70)
    print("COMBINATION SUM - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/combination-sum")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, target, expected_combos in test_cases:
            try:
                result = func(nums[:], target)
                got = normalize(result)
                exp = sorted(expected_combos)
                if got != exp:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, target={target}, expected={exp}, got={got}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: nums={nums}, target={target}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
