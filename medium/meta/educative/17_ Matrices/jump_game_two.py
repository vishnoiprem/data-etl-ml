"""
Jump Game II
Medium | 30 min

Given an array of non-negative integers nums, you are initially
positioned at the first index. Each element nums[i] represents the
maximum jump length from that position. Return the minimum number
of jumps to reach nums[n-1]. You may assume you can always reach
the last index.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/jump-game-ii

Examples:
    [2,3,1,1,4] -> 2   (0 -> 1 -> 4)
    [2,3,0,1,4] -> 2
    [1,2,3]     -> 2   (0 -> 1 -> 2)
    [0]         -> 0   (already at end)
    [1]         -> 0
    [2,0,0]     -> 1
    [5,0,0,0,0] -> 1

Constraints:
- 1 <= nums.length <= 10^3
- 0 <= nums[i] <= 10^3
- Always reachable.

KEY INSIGHT:
Greedy BFS-style layers. Each "jump" expands the reachable range.
- cur_end = farthest reach within current jump.
- next_end = max reach we can achieve in ONE more jump.
- When i == cur_end, we need a new jump (count++), update cur_end = next_end.

Time:  O(n) — single pass.
Space: O(1) — constant.
"""


# =============================================================================
# WAY 1: Greedy BFS layers (BEST - Memorize!)
# =============================================================================
def jump_1(nums):
    """
    Greedy BFS-layers. Each jump expands the reachable range.
    At each index i within current jump (cur_end), update next_end.
    When i == cur_end, increment count and start new jump.
    """
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    cur_end = 0  # farthest index reachable in current number of jumps.
    next_end = 0  # farthest index reachable in one more jump.
    for i in range(n - 1):  # don't need to consider the last index.
        next_end = max(next_end, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = next_end
    return jumps


# =============================================================================
# WAY 2: Greedy BFS with explicit max
# =============================================================================
def jump_2(nums):
    """Same as Way 1, more explicit variable names."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    current_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
    return jumps


# =============================================================================
# WAY 3: Greedy with single variable
# =============================================================================
def jump_3(nums):
    """Track only current_end and farthest."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    current_end = 0
    for i in range(len(nums) - 1):
        # Update farthest.
        current_end = max(current_end, i + nums[i])
        # When we reach current boundary, take a jump.
        if i == current_end - (current_end - i):  # confusing — bad
            jumps += 1
    return jumps


# Simplified Way 3 (correct):
def jump_3(nums):
    """Track farthest reach within current number of jumps."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == end:
            jumps += 1
            end = farthest
    return jumps


# =============================================================================
# WAY 4: BFS queue with levels
# =============================================================================
def jump_4(nums):
    """Explicit BFS levels. Each level = one jump."""
    from collections import deque
    n = len(nums)
    if n <= 1:
        return 0
    visited = {0}
    queue = deque([0])
    jumps = 0
    while queue:
        for _ in range(len(queue)):
            i = queue.popleft()
            if i == n - 1:
                return jumps
            for j in range(i + 1, min(i + nums[i] + 1, n)):
                if j not in visited:
                    visited.add(j)
                    queue.append(j)
        jumps += 1
    return jumps


# =============================================================================
# WAY 5: Greedy with two pointers (slow, fast)
# =============================================================================
def jump_5(nums):
    """Same BFS-layers but as slow/fast pointer."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    slow = 0
    fast = 0
    while fast < len(nums) - 1:
        jumps += 1
        # Find max reach from [slow..fast] (the current layer).
        new_fast = 0
        for i in range(slow, fast + 1):
            new_fast = max(new_fast, i + nums[i])
        slow = fast + 1
        fast = new_fast
    return jumps


# =============================================================================
# WAY 6: DP - bottom-up
# =============================================================================
def jump_6(nums):
    """
    DP: dp[i] = min jumps to reach i.
    dp[0] = 0. dp[i] = min(dp[j] + 1) for j < i and j + nums[j] >= i.
    """
    n = len(nums)
    if n <= 1:
        return 0
    dp = [float("inf")] * n
    dp[0] = 0
    for i in range(1, n):
        for j in range(i):
            if j + nums[j] >= i:
                dp[i] = min(dp[i], dp[j] + 1)
    return dp[n - 1]


# =============================================================================
# WAY 7: DP - top-down with memoization
# =============================================================================
def jump_7(nums):
    """DFS + memo: dfs(i) = min jumps from i to end."""
    n = len(nums)
    if n <= 1:
        return 0
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def dfs(i):
        if i >= n - 1:
            return 0
        best = float("inf")
        for j in range(1, nums[i] + 1):
            if i + j < n:
                best = min(best, 1 + dfs(i + j))
        return best

    return dfs(0)


# =============================================================================
# WAY 8: Greedy - track farthest within layers
# =============================================================================
def jump_8(nums):
    """Same as Way 1 with clearer comments."""
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    cur = 0  # farthest we can reach with `jumps` jumps.
    far = 0  # farthest we can reach with `jumps+1` jumps.
    for i in range(n - 1):
        far = max(far, i + nums[i])
        if i == cur:
            jumps += 1
            cur = far
    return jumps


# =============================================================================
# WAY 9: Class OOP
# =============================================================================
class JumpSolver:
    def __init__(self, nums):
        self.nums = nums

    def solve(self):
        n = len(self.nums)
        if n <= 1:
            return 0
        jumps = 0
        cur = 0
        far = 0
        for i in range(n - 1):
            far = max(far, i + self.nums[i])
            if i == cur:
                jumps += 1
                cur = far
        return jumps


def jump_9(nums):
    return JumpSolver(nums).solve()


# =============================================================================
# WAY 10: Greedy with range expansion
# =============================================================================
def jump_10(nums):
    """Track [start, end] range of current layer."""
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    start = 0
    end = 0
    while end < n - 1:
        jumps += 1
        new_end = end
        for i in range(start, end + 1):
            new_end = max(new_end, i + nums[i])
        start = end + 1
        end = new_end
    return jumps


# =============================================================================
# WAY 11: DP array - forward
# =============================================================================
def jump_11(nums):
    """Forward DP. For each i, mark dp[j] = min(dp[j], dp[i]+1) for reachable j."""
    n = len(nums)
    if n <= 1:
        return 0
    dp = [float("inf")] * n
    dp[0] = 0
    for i in range(n):
        for j in range(i + 1, min(i + nums[i] + 1, n)):
            dp[j] = min(dp[j], dp[i] + 1)
    return dp[n - 1]


# =============================================================================
# WAY 12: Greedy - one pass with single accumulator
# =============================================================================
def jump_12(nums):
    """Greedy: layer-based counting with single-pass tracker."""
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps


# =============================================================================
# WAY 13: Recursive without memo
# =============================================================================
def jump_13(nums):
    """Brute recursion, no memo. Exponential."""
    n = len(nums)

    def dfs(i):
        if i >= n - 1:
            return 0
        best = float("inf")
        for j in range(1, nums[i] + 1):
            if i + j < n:
                best = min(best, 1 + dfs(i + j))
        return best

    return dfs(0)


# =============================================================================
# WAY 14: Iterative with min function
# =============================================================================
def jump_14(nums):
    """Use min to find farthest reachable layer by layer."""
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    cur_max = 0
    next_max = 0
    for i in range(n - 1):
        next_max = max(next_max, i + nums[i])
        if i == cur_max:
            jumps += 1
            cur_max = next_max
    return jumps


# =============================================================================
# WAY 15: Greedy with explicit jump accounting
# =============================================================================
def jump_15(nums):
    """Each iteration: count when crossing layer boundary."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    cur_end = 0
    for i in range(len(nums) - 1):
        if i + nums[i] > cur_end:
            cur_end = i + nums[i]
        if i == cur_end:
            jumps += 1
    return jumps


# Simplified (correct) Way 15:
def jump_15(nums):
    """Layer-based with explicit farthest tracking."""
    if len(nums) <= 1:
        return 0
    n = len(nums)
    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps


# =============================================================================
# WAY 16: Greedy with while instead of for
# =============================================================================
def jump_16(nums):
    """While loop version of BFS-layers."""
    if len(nums) <= 1:
        return 0
    n = len(nums)
    jumps = 0
    cur_end = 0
    farthest = 0
    i = 0
    while i < n - 1:
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
        i += 1
    return jumps


# =============================================================================
# WAY 17: DP - one variable min, sweep
# =============================================================================
def jump_17(nums):
    """For each i, sweep forward to update min jumps."""
    n = len(nums)
    if n <= 1:
        return 0
    dp = [float("inf")] * n
    dp[0] = 0
    for i in range(n - 1):
        for j in range(i + 1, min(i + nums[i] + 1, n)):
            dp[j] = min(dp[j], dp[i] + 1)
            if dp[n - 1] != float("inf") and j >= n - 1:
                break
    return dp[n - 1]


# =============================================================================
# WAY 18: BFS with set
# =============================================================================
def jump_18(nums):
    """BFS using set for visited."""
    from collections import deque
    n = len(nums)
    if n <= 1:
        return 0
    visited = set()
    visited.add(0)
    queue = deque([0])
    jumps = 0
    while queue:
        size = len(queue)
        for _ in range(size):
            i = queue.popleft()
            if i == n - 1:
                return jumps
            for j in range(i + 1, min(i + nums[i] + 1, n)):
                if j not in visited:
                    visited.add(j)
                    queue.append(j)
        jumps += 1
    return jumps


# =============================================================================
# WAY 19: Functional style
# =============================================================================
def jump_19(nums):
    """Find each layer's farthest, count layers."""
    n = len(nums)
    if n <= 1:
        return 0
    layers = []
    end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == end:
            layers.append(farthest)
            end = farthest
    return len(layers)


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def jump_20(nums):
    """
    THE ONE TO MEMORIZE.

    Greedy BFS-layers. Each "layer" is the set of indices reachable
    with the current number of jumps.
    - cur_end: farthest index reachable with current jumps.
    - farthest: farthest index reachable with one more jump.

    Iterate i=0..n-2:
      farthest = max(farthest, i + nums[i]).
      if i == cur_end: jumps += 1; cur_end = farthest.

    Return jumps.

    Time:  O(n).
    Space: O(1).
    """
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Find minimum number of jumps to reach the last index.
Each nums[i] is the max jump length from position i."

Key Insight:
"Greedy BFS-layers. Each layer = set of indices reachable
with the current number of jumps.
- cur_end: farthest index reachable with `jumps` jumps.
- farthest: farthest index reachable with `jumps+1` jumps.

Iterate i=0..n-2:
  Update farthest.
  If i == cur_end, take another jump: jumps++, cur_end = farthest."

Algorithm:
1. jumps = 0, cur_end = 0, farthest = 0.
2. For i in 0..n-2:
     farthest = max(farthest, i + nums[i]).
     if i == cur_end: jumps++; cur_end = farthest.
3. Return jumps.

Why Greedy is Optimal:
- At each layer boundary, we MUST jump.
- The farthest within current layer is the best next position
  to be at (because it covers more positions for the next layer).
- This minimizes the number of jumps.

Edge Cases:
- Single element: 0.
- All zeros except first: works (reachable by assumption).
- All same value: n // (val+1) jumps approx.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Greedy   | O(n)   | O(1)   |
| BFS      | O(n)   | O(n)   |
| DP       | O(n^2) | O(n)   |
+----------+--------+--------+

THE TRICK:
- "Layer" = set of indices reachable with K jumps.
- When reaching layer boundary, increment K.

ALTERNATE: BFS with explicit queue.
DP: dp[i] = min jumps to reach i. O(n^2) time.

RELATED:
- Jump Game (LC 55): can we reach end? Greedy bool.
- Jump Game III (LC 1306): can move both directions.
- Jump Game IV (LC 1345): BFS with jumps to same value.
- Jump Game V (LC 1340): harder.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Greedy BFS layers (BEST)", jump_1),
        ("Way 2: Greedy BFS explicit", jump_2),
        ("Way 3: Greedy single var", jump_3),
        ("Way 4: BFS queue", jump_4),
        ("Way 5: Slow/fast pointers", jump_5),
        ("Way 6: DP bottom-up", jump_6),
        ("Way 7: DP top-down memo", jump_7),
        ("Way 8: Greedy clear comments", jump_8),
        ("Way 9: Class OOP", jump_9),
        ("Way 10: Range expansion", jump_10),
        ("Way 11: DP forward", jump_11),
        ("Way 12: Greedy single var", jump_12),
        ("Way 13: Recursive no memo", jump_13),
        ("Way 14: Iterative min", jump_14),
        ("Way 15: Layer-based", jump_15),
        ("Way 16: While loop", jump_16),
        ("Way 17: DP sweep", jump_17),
        ("Way 18: BFS set", jump_18),
        ("Way 19: Functional layers", jump_19),
        ("Way 20: Final cleanest", jump_20),
    ]

    test_cases = [
        # (nums, expected)
        ([2, 3, 1, 1, 4], 2),
        ([2, 3, 0, 1, 4], 2),
        ([1, 2, 3], 2),
        ([0], 0),
        ([1], 0),
        ([2, 0, 0], 1),
        ([5, 0, 0, 0, 0], 1),
        ([1, 1, 1, 1], 3),
        ([2, 3, 1, 1, 4, 1, 1, 1], 3),
        ([10, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1),
    ]

    print("=" * 70)
    print("JUMP GAME II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/jump-game-ii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, expected in test_cases:
            try:
                result = func(nums)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: nums={nums}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)