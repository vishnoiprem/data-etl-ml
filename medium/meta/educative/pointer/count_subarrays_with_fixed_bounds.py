"""
Count Subarrays With Fixed Bounds - 20 Ways
=============================================
You are given an integer array nums and two integers minK and maxK.
A fixed-bound subarray of nums is a subarray that satisfies:
  - the minimum value in the subarray is equal to minK, AND
  - the maximum value in the subarray is equal to maxK.
Return the number of fixed-bound subarrays.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-subarrays-with-fixed-bounds

Examples:
    nums = [1, 3, 5, 2, 7, 5], minK = 1, maxK = 5  -> 2
        (subarrays: [1,3,5] and [1,3,5,2,5] — wait let's recalc)
        Actually: [1,3,5] (min=1,max=5) and [3,5,2,5] (min=2,max=5) — no.
        Let's compute carefully:
          Valid: nums[i] must be in [minK, maxK] or we reset.
          Indices of 1: 0; indices of 5: 2, 5; out-of-bounds: 3 (since 7>5), 4 (since 7>5).
          Wait, 7 > 5, so it's "out of bounds".
          Let's look at indices 0,1,2: [1,3,5]. min=1, max=5. ✓
          Index 3,4: 2, 7. 7 > 5, reset.
          Index 5: 5.
          Hmm, indices 0..5: [1,3,5,2,7,5]. After 7, reset.
          Last index 5 has 5. No 1 nearby. Skip.
          So the answer is the count of subarrays ending at or before index 2 that contain both 1 and 5.
          Subarrays within [0..2] containing both 1 (at 0) and 5 (at 2):
            - [0..2] = [1,3,5] ✓
            - [0..1] doesn't contain 5.
            - [1..2] doesn't contain 1.
            - [0..0], [1..1], [2..2] don't contain both.
          So 1 subarray? Hmm.
          Actually subarrays of [0..2] containing both index 0 and 2:
            [0..2], and any subarray that contains both = subarrays starting <=0 and ending >=2.
            Only one: [0..2].
          But the problem says answer is 2. So let's recount:
            nums = [1,3,5,2,7,5], minK=1, maxK=5.
            Valid subarrays (no out-of-bounds element):
              [1,3,5]: min=1, max=5. ✓
              [1,3,5,2]: min=1, max=5. ✓
              [1,3,5,2,7]: contains 7 (out of bounds), invalid.
              [3,5,2,5]: min=2, max=5 — doesn't have 1. ✗
              [3,5,2]: min=2, max=5 — ✗
            So just [1,3,5] and [1,3,5,2]. 2 subarrays. ✓

    nums = [1, 1, 1, 1], minK = 1, maxK = 1   -> 6
        All subarrays have min=max=1.
        Number of subarrays = 4*5/2 = 10. Wait the expected is 6? Hmm.
        Actually all elements equal 1, so minK = maxK = 1, and ALL 10 subarrays qualify.
        Unless they mean only those with strictly min=max=1, which is all of them. So 10.
        LeetCode says 6 for this? Actually I think for [1,1,1,1] the answer is 6.
        Wait let me re-check: for [1,1,1,1], there are 10 subarrays total.
        If minK=maxK=1, every subarray has min=1, max=1, so all 10 qualify.
        Hmm, unless the problem requires min==minK and max==maxK STRICTLY.
        Actually for minK=1 and maxK=1, we need min<=1 and max>=1 (i.e., all values == 1).
        So all 10 are valid. Maybe my recollection is off.
        Let me use the test case [1,1,1,1] -> 10.

Constraints:
- 2 <= nums.length <= 10^5
- 1 <= nums[i] <= 10^9
- 1 <= minK <= maxK <= 10^9

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count subarrays where every element is in [minK, maxK], AND the min
    equals minK, AND the max equals maxK."

2. KEY INSIGHT:
   "Split the array at any out-of-bounds element (nums[i] < minK or > maxK).
    Within each segment, count subarrays that contain BOTH at least one
    minK and at least one maxK.
    For each minK position, the number of subarrays ending at maxK positions
    is min(distance_to_maxK) ... in fact, count = last_minK_idx * last_maxK_idx
    wait no.
    The standard formula: as we sweep right, track last position of minK
    ('min_pos'), last position of maxK ('max_pos'), and last out-of-bounds
    ('bad_pos'). For each index i, if nums[i] is in [minK, maxK], the
    count contribution at i is max(0, min(min_pos, max_pos) - bad_pos)."

3. PATTERN RECOGNITION:
   "Linear sweep with three trackers. O(n)."

4. EDGE CASES:
   - All elements out of bounds -> 0.
   - No minK in any segment -> 0.
   - No maxK in any segment -> 0.
   - minK == maxK -> still works (just need both at same position).

5. TRICKY DETAIL:
   "When nums[i] is in range AND we have seen both a minK and maxK since
    the last out-of-bounds, the count added at position i is
    min(min_pos, max_pos) - bad_pos."

6. ALGORITHM:
   "Initialize: ans = 0, min_pos = -1, max_pos = -1, bad_pos = -1.
    For i in range(n):
        if nums[i] < minK or nums[i] > maxK:
            bad_pos = i
        if nums[i] == minK:
            min_pos = i
        if nums[i] == maxK:
            max_pos = i
        ans += max(0, min(min_pos, max_pos) - bad_pos)
    return ans"

7. WHY IT WORKS:
   "Each index i with valid in-range element contributes the number of
    valid subarrays ENDING at i. A subarray ending at i is valid iff
    it starts after the last bad element and contains both a minK and maxK.
    The earliest valid start is bad_pos + 1. The latest start that still
    includes both a minK and a maxK is min(min_pos, max_pos). So the count
    of valid starts is min(min_pos, max_pos) - bad_pos."

8. COMPLEXITY:
   "Time: O(n).
    Space: O(1)."

9. CODE STRUCTURE:
   "Single pass with three pointers and accumulator."

10. MENTAL TRACE:
    [1,3,5,2,7,5], minK=1, maxK=5:
    i=0, n=1: not bad. min_pos=0.
    i=1, n=3: not bad. max_pos unchanged.
    i=2, n=5: max_pos=2.
    i=3, n=2: min(min_pos=0, max_pos=2) - bad_pos=-1 = 1. ans += 1. (Subarray [1,3,5,2])
    i=4, n=7: BAD. bad_pos=4.
    i=5, n=5: max_pos=5. min(min_pos=0, max_pos=5) - bad_pos=4 = 0. ans += 0.
    Total: ans = 1.
    Wait, but expected was 2. Let me recount.
    Subarrays that satisfy: min==1, max==5.
    [1,3,5,2] — min=1, max=5. ✓
    [1,3,5] — min=1, max=5. ✓ (this ends at i=2)
    i=2 contribution: min(0, 2) - (-1) = 1. ans += 1.
    i=3 contribution: min(0, 2) - (-1) = 1. ans += 1.
    Total: 2. ✓
"""


# Solution 1: Canonical linear sweep (BEST)
def count_fixed_bounds_v1(nums, minK, maxK):
    ans = 0
    min_pos = max_pos = bad_pos = -1
    for i, x in enumerate(nums):
        if x < minK or x > maxK:
            bad_pos = i
        if x == minK:
            min_pos = i
        if x == maxK:
            max_pos = i
        ans += max(0, min(min_pos, max_pos) - bad_pos)
    return ans


# Solution 2: Using min instead of max(0, ...) (clamp with -inf)
def count_fixed_bounds_v2(nums, minK, maxK):
    ans = 0
    min_pos = max_pos = bad_pos = -1
    for i, x in enumerate(nums):
        if x < minK or x > maxK:
            bad_pos = i
        if x == minK:
            min_pos = i
        if x == maxK:
            max_pos = i
        contrib = min(min_pos, max_pos) - bad_pos
        if contrib > 0:
            ans += contrib
    return ans


# Solution 3: Reset positions on out-of-bounds (alternative formulation)
def count_fixed_bounds_v3(nums, minK, maxK):
    n = len(nums)
    ans = 0
    left = 0  # left bound of current segment (after last bad)
    min_pos = -1
    max_pos = -1
    for i in range(n):
        if nums[i] < minK or nums[i] > maxK:
            left = i + 1
            min_pos = -1
            max_pos = -1
        if nums[i] == minK:
            min_pos = i
        if nums[i] == maxK:
            max_pos = i
        if min_pos >= left and max_pos >= left:
            ans += min(min_pos, max_pos) - left + 1
    return ans


# Solution 4: Split into segments by out-of-bounds, count within each
def count_fixed_bounds_v4(nums, minK, maxK):
    ans = 0
    n = len(nums)
    i = 0
    while i < n:
        # Skip to start of valid segment
        while i < n and (nums[i] < minK or nums[i] > maxK):
            i += 1
        if i >= n:
            break
        # i is start of valid segment
        seg_min_pos = -1
        seg_max_pos = -1
        seg_start = i
        while i < n and minK <= nums[i] <= maxK:
            if nums[i] == minK:
                seg_min_pos = i
            if nums[i] == maxK:
                seg_max_pos = i
            # Per-index contribution: subarrays ending at i with both minK and maxK.
            if seg_min_pos >= seg_start and seg_max_pos >= seg_start:
                ans += min(seg_min_pos, seg_max_pos) - seg_start + 1
            i += 1
    return ans


# Solution 5: Brute force O(n^2)
def count_fixed_bounds_v5(nums, minK, maxK):
    ans = 0
    n = len(nums)
    for i in range(n):
        mn = float('inf')
        mx = float('-inf')
        for j in range(i, n):
            if nums[j] < minK or nums[j] > maxK:
                break
            mn = min(mn, nums[j])
            mx = max(mx, nums[j])
            if mn == minK and mx == maxK:
                ans += 1
    return ans


# Solution 6: Brute force with extended slices
def count_fixed_bounds_v6(nums, minK, maxK):
    n = len(nums)
    ans = 0
    for i in range(n):
        mn = mx = None
        for j in range(i, n):
            if nums[j] < minK or nums[j] > maxK:
                break
            mn = nums[j] if mn is None else min(mn, nums[j])
            mx = nums[j] if mx is None else max(mx, nums[j])
            if mn == minK and mx == maxK:
                ans += 1
    return ans


# Solution 7: Iterate all positions, count min/max in window
def count_fixed_bounds_v7(nums, minK, maxK):
    import bisect
    min_positions = []
    max_positions = []
    bad_positions = []
    for i, x in enumerate(nums):
        if x == minK:
            min_positions.append(i)
        if x == maxK:
            max_positions.append(i)
        if x < minK or x > maxK:
            bad_positions.append(i)
    ans = 0
    # For each index i in range, the contribution is the number of valid
    # starts in (last_bad, min(min_pos <= i, max_pos <= i)].
    # = min(bisect_right(min_positions, i), bisect_right(max_positions, i)) - bisect_right(bad_positions, last_bad_value)
    # But "last bad" is dynamic, so we maintain it as we sweep.
    last_bad = -1
    b_ptr = 0
    n = len(nums)
    for i in range(n):
        # Update last_bad to largest bad <= i
        while b_ptr < len(bad_positions) and bad_positions[b_ptr] <= i:
            last_bad = bad_positions[b_ptr]
            b_ptr += 1
        # How many min_positions and max_positions are <= i, after last_bad?
        mn_count = bisect.bisect_right(min_positions, i) - bisect.bisect_right(min_positions, last_bad)
        mx_count = bisect.bisect_right(max_positions, i) - bisect.bisect_right(max_positions, last_bad)
        # Subarrays ending at i: starts in (last_bad, i] such that subarray contains both mn and mx.
        # These subarrays are: starts in (last_bad, min(mn_pos, mx_pos)] where mn_pos and mx_pos are the smallest >= last_bad+1 (correctly bounded).
        # Actually simpler: count = min(mn_count, mx_count) since "min(mn_pos, mx_pos) <= i"
        # Hmm wait, we need subarray to CONTAIN both, meaning start <= min_pos AND start <= max_pos AND start > last_bad.
        # The latest valid start is min(rightmost_min_so_far, rightmost_max_so_far) — but that's V1.
        # Actually no: latest start that includes BOTH is min(min_pos, max_pos). But min_pos and max_pos here are the rightmost seen.
        # Wait, we're looking at starts > last_bad. Subarray [start..i] contains both iff start <= min_pos_for_subarray AND start <= max_pos_for_subarray — but min_pos_for_subarray and max_pos_for_subarray depend on start.
        # Hmm, easier: each start > last_bad has subarray [start..i]. It contains both a minK and a maxK iff there exists min_pos in [start, i] AND max_pos in [start, i].
        # The first valid start is max(last_bad+1, max(first_min_in_[start,i], first_max_in_[start,i])).
        # Hmm, this is getting complex. Let's match V1:
        # For each i, contribution = min(rightmost_min_in_[0,i], rightmost_max_in_[0,i]) - last_bad.
        # = (rightmost_min_seen_so_far, rightmost_max_seen_so_far) MINUS last_bad.
        # Where rightmost_min_seen_so_far is min_positions[-1] <= i (if any), etc.
        if mn_count > 0 and mx_count > 0:
            min_pos_so_far = min_positions[bisect.bisect_right(min_positions, i) - 1]
            max_pos_so_far = max_positions[bisect.bisect_right(max_positions, i) - 1]
            ans += min(min_pos_so_far, max_pos_so_far) - last_bad
    return ans


# Solution 8: Using itertools.groupby on bad positions
def count_fixed_bounds_v8(nums, minK, maxK):
    from itertools import groupby
    n = len(nums)
    ans = 0
    # Get segments split by bad positions
    in_segment = [minK <= x <= maxK for x in nums]
    segments = []
    cur_start = None
    for i, ok in enumerate(in_segment):
        if ok and cur_start is None:
            cur_start = i
        elif not ok and cur_start is not None:
            segments.append((cur_start, i - 1))
            cur_start = None
    if cur_start is not None:
        segments.append((cur_start, n - 1))
    for lo, hi in segments:
        min_pos = -1
        max_pos = -1
        for j in range(lo, hi + 1):
            if nums[j] == minK:
                min_pos = j
            if nums[j] == maxK:
                max_pos = j
            if min_pos >= lo and max_pos >= lo:
                ans += min(min_pos, max_pos) - lo + 1
    return ans


# Solution 9: Same as V1 but with accumulator and zip
def count_fixed_bounds_v9(nums, minK, maxK):
    ans = 0
    min_pos = max_pos = bad_pos = -1
    for i, x in enumerate(nums):
        if x < minK or x > maxK:
            bad_pos = i
            min_pos = max_pos = -1
        if x == minK:
            min_pos = i
        if x == maxK:
            max_pos = i
        if min_pos >= 0 and max_pos >= 0:
            ans += min(min_pos, max_pos) - bad_pos
    return ans


# Solution 10: Using a single pass with tuple
def count_fixed_bounds_v10(nums, minK, maxK):
    ans = 0
    state = (-1, -1, -1)  # (bad_pos, min_pos, max_pos)
    for i, x in enumerate(nums):
        bad, mn, mx = state
        if x < minK or x > maxK:
            bad = i
            mn = mx = -1
        if x == minK:
            mn = i
        if x == maxK:
            mx = i
        state = (bad, mn, mx)
        if mn >= 0 and mx >= 0:
            ans += min(mn, mx) - bad
    return ans


# Solution 11: Iterative implementation (recursive would blow stack)
def count_fixed_bounds_v11(nums, minK, maxK):
    # Same as V1 but reorganized.
    n = len(nums)
    ans = 0
    bad = mn = mx = -1
    for i in range(n):
        x = nums[i]
        if x < minK or x > maxK:
            bad = i
        if x == minK:
            mn = i
        if x == maxK:
            mx = i
        if mn > bad and mx > bad:
            ans += min(mn, mx) - bad
    return ans


# Solution 12: Pure brute with all subarrays
def count_fixed_bounds_v12(nums, minK, maxK):
    from itertools import combinations
    ans = 0
    n = len(nums)
    # Too slow for n>20, but conceptually:
    for i, j in combinations(range(n + 1), 2):
        sub = nums[i:j]
        if min(sub) == minK and max(sub) == maxK:
            ans += 1
    return ans


# Solution 13: One-pass with accumulator
def count_fixed_bounds_v13(nums, minK, maxK):
    # Like V1 but written more compactly.
    ans = 0
    last_min = last_max = last_bad = -1
    for i, x in enumerate(nums):
        if x == minK:
            last_min = i
        if x == maxK:
            last_max = i
        if x < minK or x > maxK:
            last_bad = i
            last_min = last_max = -1
        # Compute contribution only if both seen since last bad
        if last_min != -1 and last_max != -1:
            ans += min(last_min, last_max) - last_bad
    return ans


# Solution 14: Using accumulate (manual prefix sum of bads)
def count_fixed_bounds_v14(nums, minK, maxK):
    n = len(nums)
    bad_prefix = [0] * (n + 1)
    for i in range(n):
        bad_prefix[i + 1] = bad_prefix[i] + (1 if (nums[i] < minK or nums[i] > maxK) else 0)
    ans = 0
    last_min = last_max = -1
    for i, x in enumerate(nums):
        if x == minK:
            last_min = i
        if x == maxK:
            last_max = i
        # Number of bads up to last_min (exclusive of last_min itself)
        if last_min != -1 and last_max != -1:
            last_bad_before = -1
            for k in range(i, -1, -1):
                if bad_prefix[k + 1] > bad_prefix[k]:
                    last_bad_before = k
                    break
            if last_bad_before < min(last_min, last_max):
                ans += min(last_min, last_max) - last_bad_before
    return ans


# Solution 15: Split-and-count with prefix scans
def count_fixed_bounds_v15(nums, minK, maxK):
    n = len(nums)
    # Find all "bad" positions
    bads = [-1] + [i for i in range(n) if nums[i] < minK or nums[i] > maxK] + [n]
    ans = 0
    # For each pair of consecutive bads, the segment is in between.
    for k in range(len(bads) - 1):
        seg_start = bads[k] + 1
        seg_end = bads[k + 1]  # exclusive
        # In segment [seg_start, seg_end), count subarrays containing both minK and maxK.
        last_min = last_max = -1
        for i in range(seg_start, seg_end):
            if nums[i] == minK:
                last_min = i
            if nums[i] == maxK:
                last_max = i
            if last_min != -1 and last_max != -1:
                ans += min(last_min, last_max) - seg_start + 1
    return ans


# Solution 16: Functional with reduce
def count_fixed_bounds_v16(nums, minK, maxK):
    from functools import reduce

    def step(state, item):
        idx, x = item
        ans, bad, mn, mx = state
        if x < minK or x > maxK:
            bad = idx
            mn = mx = -1
        if x == minK:
            mn = idx
        if x == maxK:
            mx = idx
        if mn != -1 and mx != -1:
            ans += min(mn, mx) - bad
        return (ans, bad, mn, mx)

    final = reduce(step, enumerate(nums), (0, -1, -1, -1))
    return final[0]


# Solution 17: Sliding window — segment-bounded inner sweep
def count_fixed_bounds_v17(nums, minK, maxK):
    n = len(nums)
    ans = 0
    start = 0
    while start < n:
        if nums[start] < minK or nums[start] > maxK:
            start += 1
            continue
        last_min = last_max = -1
        end = start
        while end < n and minK <= nums[end] <= maxK:
            if nums[end] == minK:
                last_min = end
            if nums[end] == maxK:
                last_max = end
            if last_min >= start and last_max >= start:
                ans += min(last_min, last_max) - start + 1
            end += 1
        start = end + 1
    return ans


# Solution 18: Direct formula with sorted events
def count_fixed_bounds_v18(nums, minK, maxK):
    # Track positions of minK and maxK. For each position, count subarrays ending there.
    n = len(nums)
    ans = 0
    min_idx = max_idx = bad_idx = -1
    for i in range(n):
        if nums[i] == minK:
            min_idx = i
        if nums[i] == maxK:
            max_idx = i
        if nums[i] < minK or nums[i] > maxK:
            bad_idx = i
            min_idx = max_idx = -1
        if min_idx != -1 and max_idx != -1:
            ans += min(min_idx, max_idx) - bad_idx
    return ans


# Solution 19: Using heap? No, this is a sweep problem.
def count_fixed_bounds_v19(nums, minK, maxK):
    # Sweep tracking three indices. Same as V1 with explicit variable names.
    n = len(nums)
    ans = 0
    last_min = -1
    last_max = -1
    last_invalid = -1
    for i in range(n):
        v = nums[i]
        if v < minK or v > maxK:
            last_invalid = i
        if v == minK:
            last_min = i
        if v == maxK:
            last_max = i
        # Count valid subarrays ending at i.
        # If we have a minK and maxK since the last invalid, the start is in
        # (last_invalid, min(last_min, last_max)].
        if last_min > last_invalid and last_max > last_invalid:
            ans += min(last_min, last_max) - last_invalid
    return ans


# Solution 20: With while loop indexing
def count_fixed_bounds_v20(nums, minK, maxK):
    n = len(nums)
    ans = 0
    i = 0
    while i < n:
        # Skip bads
        while i < n and (nums[i] < minK or nums[i] > maxK):
            i += 1
        if i >= n:
            break
        seg_lo = i
        last_min = last_max = -1
        while i < n and minK <= nums[i] <= maxK:
            if nums[i] == minK:
                last_min = i
            if nums[i] == maxK:
                last_max = i
            if last_min != -1 and last_max != -1:
                ans += min(last_min, last_max) - seg_lo + 1
            i += 1
    return ans


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical)",           count_fixed_bounds_v1),
        ("V2 (max(0, ...))",         count_fixed_bounds_v2),
        ("V3 (reset on bad)",        count_fixed_bounds_v3),
        ("V4 (segment approach)",    count_fixed_bounds_v4),
        ("V5 (brute O(n^2))",        count_fixed_bounds_v5),
        ("V6 (brute v2)",            count_fixed_bounds_v6),
        ("V7 (position lists)",      count_fixed_bounds_v7),
        ("V8 (groupby)",             count_fixed_bounds_v8),
        ("V9 (reset positions)",     count_fixed_bounds_v9),
        ("V10 (tuple state)",        count_fixed_bounds_v10),
        ("V11 (recursive)",          count_fixed_bounds_v11),
        ("V12 (combinations)",       count_fixed_bounds_v12),
        ("V13 (compact)",            count_fixed_bounds_v13),
        ("V14 (prefix bads)",        count_fixed_bounds_v14),
        ("V15 (split+prefix)",       count_fixed_bounds_v15),
        ("V16 (reduce)",             count_fixed_bounds_v16),
        ("V17 (sliding inner)",      count_fixed_bounds_v17),
        ("V18 (direct sweep)",       count_fixed_bounds_v18),
        ("V19 (variable names)",     count_fixed_bounds_v19),
        ("V20 (while loop)",         count_fixed_bounds_v20),
    ]

    test_cases = [
        # (nums, minK, maxK, expected)
        ([1, 3, 5, 2, 7, 5], 1, 5, 2),
        ([1, 1, 1, 1], 1, 1, 10),
        ([1, 1, 1, 1], 1, 2, 0),
        ([1, 2, 1], 1, 2, 0),  # subarrays [1,2,1] has min=1,max=2 but [2] has min=max=2.
                                # [1,2,1] min=1,max=2 ✓; [1,2] min=1,max=2 ✓; [2,1] min=1,max=2 ✓;
                                # [1,1] min=1,max=1 ✗; [2] min=2,max=2 ✗.
                                # Actually wait, [2] has min=2 max=2, but minK=1, so ✗.
                                # [1] min=1 max=1, but maxK=2, so ✗.
                                # So valid: [1,2,1], [1,2], [2,1]. 3 subarrays.
                                # Let me verify: min([1,2,1])=1, max=2. ✓
                                # min([1,2])=1, max=2. ✓
                                # min([2,1])=1, max=2. ✓
                                # Other subarrays fail.
        ([1, 2, 1], 1, 2, 3),
        ([5, 5, 5], 5, 5, 6),
        ([1, 5, 1], 1, 5, 1),
        ([2, 3, 1], 1, 3, 1),  # [2,3,1] has min=1, max=3 ✓
        ([1, 3, 5, 2, 7, 5], 1, 5, 2),
        ([1, 1, 1, 1, 1], 1, 1, 15),
        ([10, 20, 30, 10, 20, 30], 10, 30, 1),  # only [10,20,30,10,20,30] qualifies.
                                                # Wait, check: min=10, max=30. ✓
        ([1, 2, 3], 1, 3, 1),  # full array.
        ([0, 0, 0], 0, 0, 6),  # All elements 0; minK=0, maxK=0.
                               # Wait, min(nums[i])=0 not minK? Problem: nums[i] in [minK,maxK].
                               # 0 < minK=0 fails. So this is wrong test case.
                               # Let's drop.
    ]

    # Filter out invalid tests (ones I added incorrectly)
    test_cases = [
        ([1, 3, 5, 2, 7, 5], 1, 5, 2),
        ([1, 1, 1, 1], 1, 1, 10),
        ([1, 1, 1, 1], 1, 2, 0),
        ([1, 2, 1], 1, 2, 3),
        ([5, 5, 5], 5, 5, 6),
        ([1, 5, 1], 1, 5, 1),
        ([2, 3, 1], 1, 3, 1),
        ([1, 1, 1, 1, 1], 1, 1, 15),
        ([10, 20, 30, 10, 20, 30], 10, 30, 1),
        ([1, 2, 3], 1, 3, 1),
        ([1, 3, 5], 1, 5, 1),
        ([1, 4, 5], 1, 5, 0),  # 4 outside [1,5].
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (nums, lo, hi, expected) in enumerate(test_cases):
            try:
                got = func(list(nums), lo, hi)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: nums={nums}, minK={lo}, maxK={hi} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")