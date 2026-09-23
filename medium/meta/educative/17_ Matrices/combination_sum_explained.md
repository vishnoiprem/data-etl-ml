# Combination Sum — 0.0001% Expert Guide

> **LeetCode 39** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/combination-sum
> **Problem:** `combinationSum(nums, target)` — all unique combinations summing to target.

---

## 📋 WHAT THE QUESTION ASKS

Given distinct integers `nums` and integer `target`, return all unique combinations of `nums` (with unlimited reuse) that sum to `target`.

### Constraints
- `1 <= nums.length <= 30`
- `2 <= nums[i] <= 40`
- `1 <= target <= 40`
- All `nums[i]` distinct.

### Examples
```
nums=[2,3,6,7], target=7 -> [[2,2,3],[7]]
nums=[2,3,5], target=8   -> [[2,2,2,2],[2,3,3],[3,5]]
nums=[2], target=1       -> []
nums=[2,5,3], target=9   -> [[2,2,2,3],[2,2,5],[3,3,3]]
```

### Why This Is "Medium"
- Backtracking with index progression.
- Combinations, not permutations.
- Reuse allowed.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Find all combos summing to target. Each nums[i] reusable unlimited times."

### Step 2: KEY INSIGHT — Backtracking with Start (5 min)
> "Sort nums. Backtrack(remain, start, path):
> - If remain == 0: save path.
> - For i in [start, n):
>     - If nums[i] > remain: break (sorted -> skip rest).
>     - Pick nums[i], recurse with i (REUSE allowed).
>     - Undo (pop).
>
> The 'start' index prevents reordering duplicates (e.g., [2,3] vs [3,2])."

### Step 3: Why Recurse with `i`, Not `i+1` (3 min)
> "i+1 means 'next number', no reuse.
> i means 'same number again', reuse allowed.
>
> The problem allows reuse, so use `i` (not `i+1`)."

### Step 4: Algorithm (3 min)
```
1. Sort nums.
2. result = [].
3. def dfs(remain, start, path):
     if remain == 0: result.append(path[:]); return
     for i in range(start, len(nums)):
       if nums[i] > remain: break
       path.append(nums[i])
       dfs(remain - nums[i], i, path)
       path.pop()
4. dfs(target, 0, []).
5. Return result.
```

### Step 5: Edge Cases (2 min)
- target < min(nums): return [].
- Single element matches: [[nums[0] * count]].
- target == 0: [[]] if allowed.
- Very large target: exponential time.

### Step 6: Code It (3 min)

```python
def combinationSum(nums, target):
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
```

### Step 7: Verify (2 min)
For nums=[2,3,6,7], target=7:
- dfs(7, 0, []):
  - i=0, n=2: dfs(5, 0, [2]):
    - i=0, n=2: dfs(3, 0, [2,2]):
      - i=0, n=2: dfs(1, 0, [2,2,2]) -> fails
      - i=1, n=3: dfs(0, 1, [2,2,3]) -> MATCH ✓
  - i=1, n=3: dfs(4, 1, [3]) -> fails
  - i=2, n=6: dfs(1, 2, [6]) -> fails
  - i=3, n=7: dfs(0, 3, [7]) -> MATCH ✓

Result: [[2,2,3], [7]] ✓

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **Backtracking with start:** Best, O(N^(T/M)) time, O(T/M) space.
> 2. **DP building combos:** O(N*T) time, O(T*K) space.
> 3. **BFS:** Same as DP, iterative.
>
> I'll use backtracking."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find all unique combinations of nums (with reuse) summing
to target.

KEY INSIGHT: Backtracking with index progression.
1. Sort nums (early termination when nums[i] > remain).
2. dfs(remain, start, path):
   - If remain == 0: save path.
   - For i in [start, n):
       - If nums[i] > remain: break.
       - Pick nums[i], recurse with i (REUSE allowed).
       - Pop (backtrack).
3. The 'start' prevents permutations/duplicates.

ALGORITHM:
1. Sort nums.
2. Backtrack from start=0.
3. Return collected combos.

COMPLEXITY: O(N^(T/M)) time, O(T/M) recursion space.

EDGE CASES:
- target < min(nums): return [].
- Single element matching.

THE TRICK:
- Sort enables early break.
- Recurse with i (not i+1) for reuse.
- start prevents reordering duplicates.

ALTERNATE: DP — build combos for each sum incrementally.
DP[i] = list of combos summing to i.
For each n in nums:
  For i from n to target:
    DP[i] += [combo + [n] for combo in DP[i-n] if combo[-1] <= n]

RELATED:
- Combination Sum II (LC 40): no reuse, has duplicates in nums.
- Combination Sum III (LC 216): exactly k numbers.
- Combination Sum IV (LC 377): permutations.
- Coin Change (LC 322): min coins.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Backtracking (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Standard backtrack | O(N^T/M) | O(T/M) | **THE ANSWER** |
| 6 | Class OOP | O(N^T/M) | O(T/M) | Reusable |
| 15 | Clean start backtrack | O(N^T/M) | O(T/M) | Variant |
| 20 | Final cleanest | O(N^T/M) | O(T/M) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Iterative / DP Building

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Iterative DP | O(N*T*K) | O(T*K) | Iterative |
| 4 | BFS | O(...) | O(T*K) | Iterative |
| 10 | 2D DP check | O(N*T*K) | O(T*K) | Variant |
| 12 | DP + dedupe | O(N*T*K) | O(T*K) | Educational |
| 17 | Numpy DP | O(N*T*K) | O(T*K) | Vectorized |

### 🟠 TIER 3: Memoization

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Memoized DFS | O(N*T) | O(N*T) | Top-down |
| 16 | Memo dict | O(N*T) | O(N*T) | Educational |

### 🔵 TIER 4: Specialized / Educational

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | No sort | O(N^T/M) | O(T/M) | Variant |
| 7 | Pick/skip | O(N^T/M) | O(T/M) | Educational |
| 8 | Tail recursion | O(N^T/M) | O(T/M) | Variant |
| 9 | Generator | O(N^T/M) | O(T/M) | Generator |
| 11 | Itertools CWR | O(...) | O(...) | Educational |
| 13 | Brute combos | O(...) | O(...) | Reference |
| 14 | Seen-set backtrack | O(N^T/M) | O(T/M) | Educational |
| 18 | Stack DFS | O(N^T/M) | O(T/M) | Iterative |
| 19 | Iter deepening | O(N^T/M) | O(T/M) | Educational |

---

## 💎 THE 11-LINE SOLUTION (Memorize!)

```python
def combinationSum(nums, target):
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
```

**Time:** `O(N^(T/M))` where T=target, M=min(nums).
**Space:** `O(T/M)` recursion depth.

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Start Index = Combinations, Not Permutations

> Without `start`, [2,3] and [3,2] would both appear.
> With `start`, only [2,3] (after picking 2, pick from index ≥ 0).

**Connection to:**
- **Combinations vs permutations:** Start discipline.
- **LC 39 vs LC 377:** Same algo, different loop.

### Insight 2: Sort Enables Pruning

> Without sort, can't break on nums[i] > remain.
> Saves exponential time in worst case.

**Connection to:**
- **Optimization:** Preprocessing.
- **Common trick:** Always sort.

### Insight 3: Recurse with `i`, Not `i+1`

> For LC 39 (reuse allowed), recurse with i.
> For LC 40 (no reuse), recurse with i+1.

Tiny index difference, different problem.

**Connection to:**
- **Problem family:** Same/similar.
- **Index arithmetic:** Critical.

### Insight 4: Path is Mutable, Use `path[:]` to Save

> `result.append(path)` saves REFERENCE. `path[:]` saves COPY.
> Without copy, all saved paths point to same list (modified later).

**Connection to:**
- **Python semantics:** Reference vs value.
- **Common mistake:** Easy to miss.

### Insight 5: DP Variant Skips Sort, Adds Dedupe

> DP builds combos for each sum. Order-independent, but dups possible.
> Then need set-based dedup.

**Connection to:**
- **DP vs backtrack:** Different approach.
- **Dedupe:** Common need.

### Insight 6: Why BFS Works

> BFS explores states (sum, combo). Each state reachable in O(1).
> Reaches target via combinations.

**Connection to:**
- **Multiple views:** BFS = iterative DP.
- **Graph algorithms:** State exploration.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Subset sum partitioning** | Reaching target sums |
| **Knapsack variants** | Item combinations |
| **Financial portfolios** | Sum to budget |
| **Recipe scaling** | Ingredient combos |
| **Resource allocation** | Reaching limits |
| **Cryptographic keys** | Sum-based |

**Subset sum** is the canonical use case.

### Insight 8: Complexity is Exponential

> Worst case: all nums[0] = 1, target = T. Then T+1 combos.
> Time is O(T^N / T!) in worst case.

For target=40, this is manageable.

**Connection to:**
- **Exponential time:** Standard for this problem.
- **Constraint analysis:** T=40 keeps it reasonable.

### Insight 9: Connection to Coin Change

> Coin Change = min coins summing to amount (memoized DP).
> Combination Sum = list all combos.

Both: unlimited reuse.

**Connection to:**
- **Problem family:** Unbounded knapsack.
- **Different output:** Min vs all lists.

### Insight 10: Itertools.combinations_with_replacement

> Python's `itertools.combinations_with_replacement` enumerates
> CWR sets. Iterate up to k = T/min, filter by sum.

**Connection to:**
- **Standard library:** Reusable.
- **Educational:** Explore alternative.

### Insight 11: Why Path is Shared (Not Copied)

> path is mutable for efficient append/pop.
> result needs copies (path[:]).

**Connection to:**
- **Memory:** Mutable shared.
- **Correctness:** Copy on save.

### Insight 12: LC 39 vs LC 40

> LC 39: nums distinct, reuse allowed. Recurse with i.
> LC 40: nums may have dups, no reuse. Recurse with i+1, skip dups.

Tiny changes, different problems.

**Connection to:**
- **Problem variants:** Close family.
- **Edge cases:** Easy to confuse.

### Insight 13: When Memo Beats Sort

> Memoize on (start, remain) instead of sorting.
> Same state space but no early termination.

**Connection to:**
- **Trade-off:** Memory vs time.
- **Both work:** Pick by preference.

### Insight 14: Why Start Parameter

> Without start, we'd generate (1+2+3) and (1+3+2) etc.
> With start, only one canonical ordering per combo.

**Connection to:**
- **Canonicalization:** Order enforcement.
- **Standard technique:** Always include.

### Insight 15: Tail Recursion Variant

> Some problems are best solved by counting how many times to pick
> each num, then recursing on next num.

Educational but less efficient.

**Connection to:**
- **Different views:** Same problem.
- **Educational:** Insight into structure.

### Insight 16: Stack-Based = No Recursion Limit

> Python default recursion limit (1000). For target=1000, may exceed.
> Convert to iterative stack-based DFS.

**Connection to:**
- **Practical concern:** Limits.
- **Iteration:** Safer for large targets.

---

## 🧪 TEST CASES

| `nums` | `target` | Expected Count | Note |
|--------|----------|----------------|------|
| `[2,3,6,7]` | 7 | 2 | Standard |
| `[2,3,5]` | 8 | 3 | Standard |
| `[2]` | 1 | 0 | Impossible |
| `[1]` | 1 | 1 | Single |
| `[1]` | 2 | 1 | Reuse |
| `[2,5,3]` | 9 | 3 | Unsorted |
| `[3,1,2]` | 4 | 4 | All combos |
| `[2,3,5]` | 1 | 0 | Below min |
| `[3,5,7]` | 15 | 3 | Larger |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Backtracking** | **O(N^(T/M))** | **O(T/M)** | **✅ BEST** |
| Iterative DP | O(N*T*K) | O(T*K) | ✅ Iterative |
| Memoized | O(N*T) | O(N*T) | ✅ Top-down |
| Brute itertools | O(N^(T/M)) | O(T/M) | ✅ Stdlib |

T=target, M=min(nums), K=avg combos.

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Combination Sum II (LC 40) | Backtrack, no reuse | https://leetcode.com/problems/combination-sum-ii/ |
| Combination Sum III (LC 216) | Backtrack, k numbers | https://leetcode.com/problems/combination-sum-iii/ |
| Combination Sum IV (LC 377) | Permutations | https://leetcode.com/problems/combination-sum-iv/ |
| Coin Change (LC 322) | Memoized DP | https://leetcode.com/problems/coin-change/ |
| Combination Sum (LC 39) | **This problem** | https://leetcode.com/problems/combination-sum/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Sort + backtrack** with start index.
2. **Recurse with `i`** for reuse, `i+1` for no reuse.
3. **`path[:]`** for deep copy on save.
4. **Break on nums[i] > remain** after sort.
5. **Subset sum** is canonical application.
6. **LC 39 vs 40 vs 216**: tiny index differences.
7. **Exponential worst-case** but T=40 OK.
8. **DP variant** for iterative solution.
9. **seen-set** for edge cases with dup nums.
10. **itertools.combinations_with_replacement** as backup.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Subset sum** | Reaches target sums |
| **Knapsack** | Item combinations |
| **Financial** | Portfolio sums |
| **Recipe scaling** | Ingredient combos |
| **Resource allocation** | Reaching limits |
| **Cryptography** | Sum-based keys |
| **Chemistry** | Molecule combos |
| **Inventory** | Stock combinations |
| **Coin change** | Making change |
| **Combinatorial game** | Move combos |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive backtracking with start in 90 seconds
- [x] Can code the 11-line solution in 60 seconds
- [x] Know complexity: O(N^(T/M)) time, O(T/M) space
- [x] Know why sort enables early break
- [x] Know why recurse with `i` (not `i+1`)
- [x] Know why `path[:]` for deep copy
- [x] Know related problems (LC 40, 216, 377, 322)
- [x] Know LC 39 vs LC 40 difference
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 12 minutes.
**Lines of code to write:** 11.
**Insight:** "Sort + backtrack. Start index prevents duplicates. Recurse with i (not i+1) for reuse."
