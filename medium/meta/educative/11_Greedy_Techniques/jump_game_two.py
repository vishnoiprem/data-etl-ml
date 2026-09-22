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
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT JUMP GAME II:

1. UNDERSTAND THE PROBLEM:
   "Min jumps from index 0 to index n-1. Each nums[i] is max jump length."

2. KEY OBSERVATION:
   "Each jump expands the reachable region.
   After K jumps, we can reach all indices in 'layer K'.
   Min jumps = number of layers until we reach n-1."

3. GREEDY INSIGHT (BFS-layers):
   "Within a layer, we can be at ANY of its indices.
   But we should choose the index that maximizes the next layer's reach.
   That's the 'farthest' position within current layer."

4. TWO-POINTER VARIABLE VIEW:
   - cur_end: farthest index reachable with current jumps.
   - farthest: farthest index reachable with one more jump.
   - When i == cur_end, we've exhausted current layer: take a jump,
     update cur_end = farthest.

5. EDGE CASES:
   - Single element: 0 (already at end).
   - Direct reach (nums[0] >= n-1): 1 jump.
   - All reachable by problem guarantee.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Greedy   | O(n)   | O(1)   |
   | BFS      | O(n)   | O(n)   |
   | DP       | O(n^2) | O(n)   |
   +----------+--------+--------+

7. WHY GREEDY > DP:
   - We don't need exact paths, only layer counts.
   - DP O(n^2) is overkill.
   - Greedy BFS-layers achieves O(n) with O(1) space.
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
    cur_end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps


# =============================================================================
# WAY 2: Greedy with explicit variable names
# =============================================================================
def jump_2(nums):
    """Same as Way 1, more explicit variable names."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    current_end = 0
    far_reach = 0
    for i in range(len(nums) - 1):
        far_reach = max(far_reach, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = far_reach
    return jumps


# =============================================================================
# WAY 3: Slow/fast pointers (layered)
# =============================================================================
def jump_3(nums):
    """Slow/fast pointer version of BFS-layers."""
    if len(nums) <= 1:
        return 0
    jumps = 0
    slow = 0
    fast = 0
    while fast < len(nums) - 1:
        jumps += 1
        new_fast = 0
        for i in range(slow, fast + 1):
            new_fast = max(new_fast, i + nums[i])
        slow = fast + 1
        fast = new_fast
    return jumps


# =============================================================================
# WAY 4: BFS with explicit queue
# =============================================================================
def jump_4(nums):
    """Explicit BFS levels using deque. Each level = one jump."""
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
# WAY 5: DP - bottom-up
# =============================================================================
def jump_5(nums):
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
# WAY 6: DP - top-down with memoization
# =============================================================================
def jump_6(nums):
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
# WAY 7: Class OOP
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


def jump_7(nums):
    return JumpSolver(nums).solve()


# =============================================================================
# WAY 8: Range expansion approach
# =============================================================================
def jump_8(nums):
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
# WAY 9: Brute force recursion (exponential)
# =============================================================================
def jump_9(nums):
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
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def jump_10(nums):
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
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Greedy BFS layers (BEST)", jump_1),
        ("Way 2: Explicit variable names", jump_2),
        ("Way 3: Slow/fast pointers", jump_3),
        ("Way 4: BFS queue", jump_4),
        ("Way 5: DP bottom-up", jump_5),
        ("Way 6: DP top-down memo", jump_6),
        ("Way 7: Class OOP", jump_7),
        ("Way 8: Range expansion", jump_8),
        ("Way 9: Recursive no memo", jump_9),
        ("Way 10: Final cleanest", jump_10),
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
    print("JUMP GAME II - 10 IMPLEMENTATIONS")
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
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)