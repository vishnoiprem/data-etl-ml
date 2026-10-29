# Number of Longest Increasing Subsequence

## Problem
Given an integer array `nums`, return the **count** of strictly
increasing subsequences whose length equals the **maximum** LIS length.

## Approach: Parallel DP

Track two parallel arrays as we process the array left-to-right:
- `length[i]` = length of the longest increasing subsequence **ending at** index `i`
- `count[i]`  = number of such longest subsequences ending at `i`

### Transition
For each pair `j < i`:
- If `nums[j] < nums[i]`, we can extend any LIS ending at `j` by `nums[i]`.
- If `length[j] + 1 > length[i]`: we found a longer LIS at `i` →
  `length[i] = length[j] + 1`, `count[i] = count[j]`.
- If `length[j] + 1 == length[i]`: another LIS of the same length →
  `count[i] += count[j]`.

Otherwise (`nums[j] >= nums[i]`), skip — can't extend.

### Initialization
- `length[i] = 1` (the element alone)
- `count[i] = 1`

### Answer
Find the maximum `max_len = max(length)`, then return
`sum(count[i] for i with length[i] == max_len)`.

## Walkthrough: `[1, 3, 5, 4, 7]`

Building up:
- i=0: `(1, 1)`
- i=1: length=2, count=1  (extend 1)
- i=2: length=3, count=1  (extend 1→3)
- i=3: length=3, count=1  (extend 1→3)
- i=4: 
  - from 0 (1→7): length 2 → new max, count=1
  - from 1 (3→7): length 3 → new max, count=1 (overrides)
  - from 2 (5→7): length 4 → new max, count=1
  - from 3 (4→7): length 4 → TIE → count = 1 + 1 = 2

`max_len = 4`, only index 4 has it, count = **2** ✓

(The two LIS are `1,3,5,7` and `1,3,4,7`.)

## Complexity
- **Time:** `O(n²)` — quadratic DP
- **Space:** `O(n)`

## Edge Cases
- Empty array → 0
- Single element → 1
- All equal elements → length=1 LIS, but the answer is `n` because each element alone is a LIS of length 1
