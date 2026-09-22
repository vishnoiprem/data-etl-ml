# Delete and Earn — 0.0001% Expert Guide

> **Educative: Grokking Coding Interview in Python** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/delete-and-earn
> **Problem:** `delete_and_earn(nums)` — maximize points by picking elements while deleting adjacent values.

---

## 📋 WHAT THE QUESTION ASKS

Given `nums[]`, repeatedly:
- Pick element `nums[i]`, earn `nums[i]` points.
- Delete ALL elements with value `nums[i] - 1` or `nums[i] + 1` (earn 0 for these).

Return the maximum total points.

### Constraints
- `1 <= nums.length <= 2 * 10^4`
- `1 <= nums[i] <= 10^4`

### Examples
```
nums=[3, 4, 2]                          -> 6
  (Pick 4: +4. Pick 2: +2. Total 6.)
nums=[2, 2, 3, 3, 3]                    -> 9
  (Pick all 3's: +9. Total 9.)
nums=[1, 1, 1, 2, 2, 3, 3, 3, 3, 4]    -> 15
  (Pick all 3's: +12. Pick 1's: +3. Total 15.)
```

### Why This Is "Medium"
- Reduce to House Robber via value counting.
- O(n + max(nums)) time.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Pick element, earn its value, delete +/-1 values. Maximize earnings."

### Step 2: KEY INSIGHT — Reduce to House Robber (5 min)
> "For each value v, let points[v] = v * count(v in nums). If I pick v,
> I get points[v] and can't pick v-1 or v+1. This is House Robber on
> the points array indexed by value."

### Step 3: Why This Reduction Works (3 min)
> "When I pick v, ALL elements with value v are essentially 'taken' or
> 'not taken' as a group (since picking one v doesn't delete other v's).
> So I either take the entire group v or skip it. The choice is binary
> per value, and the constraint is 'no two adjacent values'. House Robber!"

### Step 4: Algorithm (3 min)
```
1. Compute points[v] for each value v.
2. Apply House Robber DP on points[0..max_n]:
   rob[i] = max(rob[i-1], rob[i-2] + points[i])
3. Return rob[max_n].
```

### Step 5: Edge Cases (2 min)
- Empty nums: 0.
- All same value: sum of all.
- No adjacent values in nums: sum of all.

### Step 6: Code It (3 min)

```python
def delete_and_earn(nums):
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    prev2, prev1 = 0, 0
    for p in points:
        prev2, prev1 = prev1, max(prev1, prev2 + p)
    return prev1
```

### Step 7: Verify (2 min)
For [2, 2, 3, 3, 3]:
- points = [0, 0, 4, 9, 0, ...]
- rob[0]=0, rob[1]=0, rob[2]=max(0, 0+4)=4, rob[3]=max(4, 0+9)=9. Return 9. ✓

### Step 8: Discuss Trade-offs (3 min)
> "Two approaches:
> 1. **House Robber DP:** O(n + max_n). Best.
> 2. **Brute force subsets:** O(2^n). Too slow.
>
> I'll use House Robber DP."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to maximize points by picking elements while deleting +/-1 values.

KEY INSIGHT: This is HOUSE ROBBER in disguise!
- Let points[v] = v × count(v in nums). Total value for each v.
- Picking v means I take all v's (deleting +/-1 removes v-1 and v+1).
- So I either take the entire group v or skip it.
- Constraint: no two adjacent v's. House Robber!

ALGORITHM:
1. Compute points[v] for v in [0, max_n].
2. House Robber DP: rob[i] = max(rob[i-1], rob[i-2] + points[i]).
3. Return rob[max_n].

COMPLEXITY: O(n + max(nums)) time, O(max(nums)) space.

EDGE CASES:
- Empty: 0.
- All same value: sum of all.

THE TRICK: Value-based counting turns a complex deletion problem into
the classic House Robber.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: House Robber DP (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Points array + DP (BEST) | O(n+M) | O(M) | **THE ANSWER** |
| 2 | Full DP array | O(n+M) | O(M) | Educational |
| 3 | Compact DP | O(n+M) | O(1) | **THE ONE TO MEMORIZE** |
| 4 | Counter + DP | O(n+M) | O(M) | Educational |
| 9 | Class OOP | O(n+M) | O(M) | Reusable |
| 10 | Skip/take state | O(n+M) | O(1) | Variant |
| 14 | Iterative state | O(n+M) | O(1) | Educational |
| 20 | Final cleanest | O(n+M) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Sparse DP (only distinct values)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Sort + dict DP | O(n log n + U) | O(U) | Sparse |
| 6 | Sort + tuple DP | O(n log n + U) | O(U) | Educational |
| 11 | defaultdict | O(n log n + U) | O(U) | Educational |
| 13 | Sort + group | O(n log n + U) | O(U) | Sparse variant |
| 15 | Distinct values list | O(n log n + U) | O(U) | Educational |
| 16 | House Robber explicit | O(n log n + U) | O(U) | Sparse variant |
| 18 | Sort + DP clean | O(n log n + U) | O(U) | Sparse |
| 19 | Counter greedy-like | O(n log n + U) | O(U) | Educational |

### 🟠 TIER 3: Memoization / Recursive

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 8 | Recursive memo | O(n+M) | O(M) | Top-down |
| 17 | Memo dict | O(U) | O(U) | Sparse memo |

### 🔴 TIER 4: Brute Force

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 7 | Subsets | O(2^n) | O(n) | Tiny n only |

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def delete_and_earn(nums):
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    prev2, prev1 = 0, 0
    for p in points:
        prev2, prev1 = prev1, max(prev1, prev2 + p)
    return prev1
```

**Time:** `O(n + max(nums))`
**Space:** `O(max(nums))`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Recognize the Reduction

> "Deletion of +/-1 means I commit to a group once and only once."

This binary commitment per value is the signature of House Robber.

**Connection to:**
- **Pattern recognition:** Multiple problems reduce to House Robber.
- **Reduction:** Most powerful technique in algorithms.

### Insight 2: Group by Value

> Count total points per value, then make binary decisions per value.

Sparse data → fewer values → smaller DP.

**Connection to:**
- **Compression:** Group similar items.
- **DP state design:** Choose right granularity.

### Insight 3: House Robber Variants

| Variant | Twist |
|---------|-------|
| LC 198 | Linear |
| LC 213 | Circular (first = last constraint) |
| LC 337 | Tree |
| Delete and Earn | Reduce to linear |

**Connection to:**
- **Problem family:** Many House Robber variants.
- **Adaptability:** Same DP skeleton.

### Insight 4: Why Sparse DP Helps

> If nums contains only K distinct values, you only need K states.

For sparse data, K << max(nums), saving both time and space.

**Connection to:**
- **Input distribution:** Matters for performance.
- **Sparse arrays:** Map-based DP.

### Insight 5: When to Use Full vs Sparse DP

> Full DP: O(max_n) space, fast when nums is dense.
> Sparse DP: O(K) space, faster when nums is sparse.

Choose based on `max(nums)` vs `len(set(nums))`.

**Connection to:**
- **Trade-offs:** Time vs space.
- **Problem-specific optimization:** Adapt to input.

### Insight 6: Connection to Climbing Stairs

> Both use the "skip vs take" decision.

Different mechanics, same DP skeleton.

**Connection to:**
- **DP patterns:** Reusable structures.
- **Optimization:** Same recurrence.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Investment** | Choose non-conflicting assets |
| **Scheduling** | Non-overlapping meetings |
| **Network routing** | Non-adjacent nodes |
| **Resource allocation** | Independent tasks |
| **Stock trading** | Cool-down periods |

**Investment portfolios** with non-correlated assets use similar logic.

### Insight 8: Why "Pick All" per Value

> Picking one v doesn't delete other v's. So picking v is a binary choice.

Without this property, the problem would be much harder.

**Connection to:**
- **Problem structure:** Hidden binary choice.
- **Reduction:** Identify structure.

### Insight 9: Counter vs Dictionary

> Counter is concise but slower; dict.get is faster.

For competitive programming, prefer dict.get for speed.

**Connection to:**
- **Python optimization:** Built-in vs custom.
- **Performance:** Small wins matter.

### Insight 10: Why Two Variables Suffice

> House Robber only needs the last 2 states — O(1) space.

Full DP array is unnecessary unless you need to backtrack.

**Connection to:**
- **Space optimization:** Rolling arrays.
- **DP theory:** State dependencies.

### Insight 11: Brute Force Infeasibility

> O(2^n) subsets for n=20000 is impossible.

Combinatorial insight essential.

**Connection to:**
- **Asymptotic limits:** Always check.
- **Reduction:** Avoid enumeration.

### Insight 12: Connection to Maximum Weight Independent Set

> Maximum Weight Independent Set on a path graph = House Robber.

Delete and Earn is MWIS on a path of values [0..max(nums)].

**Connection to:**
- **Graph theory:** Path graphs.
- **Independent set:** Classic problem.

### Insight 13: Edge Case: All Same Value

> points[v] = n * v, and House Robber picks it all. Total = n*v.

Verify with small examples.

**Connection to:**
- **Edge case testing:** Always include.
- **Sanity checks:** Easy cases.

### Insight 14: When to Sort vs Use Array

> Sorting: O(n log n). Array indexed by value: O(n + max_n).

For dense nums (max_n ~ n), array wins. For sparse, sorting wins.

**Connection to:**
- **Input shape:** Determines optimal approach.
- **Time complexity:** Right structure for data.

---

## 🧪 TEST CASES

| `nums` | Expected | Note |
|--------|----------|------|
| `[3, 4, 2]` | 6 | Standard |
| `[2, 2, 3, 3, 3]` | 9 | All 3's |
| `[1, 1, 1, 2, 2, 3, 3, 3, 3, 4]` | 15 | Mixed |
| `[1, 2, 3]` | 4 | Pick 1+3 |
| `[1, 2, 3, 3, 3]` | 10 | All 3's + 1 |
| `[1]` | 1 | Single |
| `[2, 2]` | 4 | Both 2's |
| `[1, 5, 1, 5]` | 12 | Two pairs |
| `[1, 2, 1, 2]` | 4 | Adjacent values |
| `[]` | 0 | Empty |
| `[5, 5, 5, 5, 5]` | 25 | All same |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **House Robber DP (full)** | **O(n+M)** | **O(M)** | **✅ BEST** |
| Sparse DP | O(n log n + U) | O(U) | ✅ For sparse |
| Brute force | O(2^n) | O(n) | ❌ Too slow |
| Memo recursive | O(M) | O(M) | ✅ Top-down |

M = max(nums), U = # distinct values.

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| House Robber (LC 198) | DP | https://leetcode.com/problems/house-robber/ |
| House Robber II (LC 213) | Circular DP | https://leetcode.com/problems/house-robber-ii/ |
| House Robber III (LC 337) | Tree DP | https://leetcode.com/problems/house-robber-iii/ |
| Max sum non-adjacent | DP | Classic problem |
| Delete and Earn (LC 740) | **This problem** | https://leetcode.com/problems/delete-and-earn/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Recognize House Robber** — many problems reduce to it.
2. **Group by value** — turns variable picking into binary decision.
3. **Two variables suffice** — O(1) space DP.
4. **Sparse optimization** — for sparse nums.
5. **O(n + max_n)** dominates.
6. **Investment portfolios** are the canonical use case.
7. **Same pattern as LC 198, 213, 337**.
8. **Independent set on path graph** = House Robber.
9. **Edge case: empty** → 0.
10. **Avoid brute force O(2^n)**.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Investment** | Non-conflicting assets |
| **Scheduling** | Non-overlapping meetings |
| **Network routing** | Non-adjacent nodes |
| **Resource allocation** | Independent tasks |
| **Stock trading** | Cool-down periods |
| **Portfolio optimization** | Correlation avoidance |
| **Job scheduling** | Compatible tasks |
| **Game theory** | Strategy selection |
| **Constraint satisfaction** | Independent choices |
| **Combinatorial optimization** | Maximum weight set |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive House Robber reduction in 60 seconds
- [x] Can code the 8-line solution in 60 seconds
- [x] Know complexity: O(n + max(nums)) time, O(max(nums)) space
- [x] Know why this reduces to House Robber
- [x] Know sparse DP variant
- [x] Know edge cases (empty, all same)
- [x] Can compare with brute force
- [x] Know related problems (LC 198, 213, 337)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 8.
**Insight:** "Count points per value (points[v] = v * count). Apply House Robber DP on the points array. Constraint: no two adjacent values can both be picked."