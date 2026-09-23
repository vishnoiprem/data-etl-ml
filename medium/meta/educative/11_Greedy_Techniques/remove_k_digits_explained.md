# Remove K Digits — 0.0001% Expert Guide

> **LeetCode 402** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/remove-k-digits
> **Problem:** `removeKdigits(num, k)` — remove k digits to form smallest number.

---

## 📋 WHAT THE QUESTION ASKS

Given string `num` representing a non-negative integer and integer `k`, remove exactly `k` digits to make the smallest possible number. Return the result as a string with no leading zeros (except the result "0").

### Constraints
- `1 <= num.length <= 10^3`
- `0 <= k <= num.length`
- num consists of digits only.

### Examples
```
num="1432219", k=3 -> "1219"  (remove 4, 3, 2)
num="10200", k=1   -> "200"   (remove the 1)
num="10", k=2      -> "0"     (remove both)
num="112", k=1     -> "11"    (remove middle 1)
num="1234567", k=3 -> "1234"  (remove last 3)
```

### Why This Is "Medium"
- Greedy monotonic stack insight.
- O(n) time, O(n) space.
- Multiple edge cases (leading zeros, empty result, all same).

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Question
> "Remove k digits, keep order, get smallest result."

### Step 2: Key Insight — Big Before Small
> "If a digit is BIGGER than the digit right after it, removing the bigger
> one ALWAYS makes the number smaller.
> Example: 1[4]3 -> 13 (smaller than 14)."

### Step 3: Greedy + Monotonic Stack
> "Maintain a stack of digits (non-decreasing from bottom to top).
> When the current digit is SMALLER than stack top, pop the top
> (remove that bigger digit). This is greedy optimal.
> If k remains after processing, drop the last k digits (they're largest)."

### Step 4: Algorithm
```
1. stack = [], iterate digits:
     while k > 0 and stack and stack[-1] > digit:
       stack.pop(); k -= 1.
     stack.append(digit).
2. If k > 0: stack = stack[:-k]  (drop from end).
3. Strip leading zeros: result = "".join(stack).lstrip("0").
4. Return result or "0" if empty.
```

### Step 5: Edge Cases
- All increasing ("12345", k=2): no pops happen, drop last 2 → "123".
- All decreasing ("54321", k=2): pop every bigger, drop 2 → "321" → wait, "54321", k=2: pop 5 (k→2), pop 4 (k→1), pop 3 (k→0). Then push 2, 1. Stack = [2,1]. Result "21".
- "10", k=1: pop '1' on '0' (k→0). Push 0. Stack=[0]. Strip: "0". ✓
- Leading zeros after removal: must strip.
- Empty result: return "0".

### Step 6: Code It

```python
def removeKdigits(num, k):
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    if k:
        stack = stack[:-k]
    result = "".join(stack).lstrip("0")
    return result if result else "0"
```

### Step 7: Verify
For "1432219", k=3:
- d='1': stack=[1], k=3
- d='4': top 1<4. Push. stack=[1,4]. k=3.
- d='3': top 4>3. Pop 4. k=2. Top 1<3. Push. stack=[1,3]. k=2.
- d='2': top 3>2. Pop 3. k=1. Top 1<2. Push. stack=[1,2]. k=1.
- d='2': top 2 not > 2. Push. stack=[1,2,2]. k=1.
- d='1': top 2>1. Pop 2. k=0. Push 1. stack=[1,2,1].
- d='9': k=0. Push. stack=[1,2,1,9].

Result: "1219" ✓

### Step 8: Trade-offs
- Stack: O(n) time, O(n) space. **BEST**.
- Brute subsets: O(C(n,k)) time, infeasible for large n.
- DP: O(n*k) time, O(n*k) space. Slower.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to remove k digits to form the smallest number."

KEY INSIGHT: Greedy monotonic stack. A digit followed by a smaller
digit should remove the larger one — it's locally and globally optimal.

ALGORITHM:
1. stack = [], iterate digits:
     while k > 0 and stack and stack[-1] > digit:
       stack.pop(); k -= 1.
     stack.append(digit).
2. If k > 0, drop last k digits.
3. Strip leading zeros; return "0" if empty.

COMPLEXITY: O(n) time, O(n) space.

EDGE CASES:
- All increasing: no pops, drop last k.
- All decreasing: pops eat up k fast.
- Leading zeros: strip.
- Empty result: "0".

WHY GREEDY = OPTIMAL:
- "Bigger-before-smaller" removal is always a win.
- Stack tracks candidates; pops guarantee monotonicity.

THE TRICK:
- "Big digit before small = remove big."
- Stack maintains the smallest possible prefix.

ALTERNATE: Brute force subsets (O(C(n,k))) or DP (O(n*k)).
Stack wins because each digit is pushed once, popped at most once.

RELATED:
- Smallest Subsequence of Distinct Characters (LC 1081).
- Find the Most Competitive Subsequence (LC 1673).
- Create Maximum Number (LC 402-like).
- Monotonic stack problems.
"""
```

---

## 💎 THE 7-LINE SOLUTION (Memorize!)

```python
def removeKdigits(num, k):
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    if k:
        stack = stack[:-k]
    result = "".join(stack).lstrip("0")
    return result if result else "0"
```

**Time:** `O(n)`
**Space:** `O(n)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Bigger-Before-Smaller = Always Remove Bigger

> If digit[i] > digit[i+1], removing digit[i] strictly reduces the number.
> This local choice is globally optimal because it doesn't affect later decisions.

**Connection to:**
- **Greedy:** Local = global.
- **Standard:** Smaller-prefix always wins.

### Insight 2: Monotonic Stack for Sequence Reduction

> Maintain stack such that digits form a non-decreasing sequence.
> When a smaller digit comes, pop larger ones (each pop is a removal).

**Connection to:**
- **Monotonic stack:** Standard technique.
- **Sliding window:** Conceptually similar.

### Insight 3: Why Strip Leading Zeros at End

> After removals, the result might have leading zeros (e.g., "10200", k=1).
> Strip them. If result is empty, return "0".

**Connection to:**
- **Edge case:** Always handle.
- **Post-processing:** Standard.

### Insight 4: k Remaining After Loop = Drop From End

> If we run out of "bigger-before-smaller" opportunities and k > 0,
> we must drop from the end (the largest remaining digits).

**Connection to:**
- **Fallback:** Last resort.
- **Standard:** Drop rightmost.

### Insight 5: Each Digit Pushed Once, Popped At Most Once

> Total work per digit: O(1) amortized.
> Loop invariant: k monotonic decreasing.
> Total time: O(n).

**Connection to:**
- **Amortized analysis:** Standard.
- **Optimal:** O(n).

### Insight 6: Connection to Smallest Subsequence of Distinct Chars

> LC 1081: Same pattern. Pop larger, keep order, distinct.
> LC 402 (this): Pop larger, keep order, no distinctness constraint.

**Connection to:**
- **Same skeleton:** Monotonic stack.
- **Constraint variation:** Reusable.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Phone numbers** | Min number with constraints |
| **Pricing** | Cheapest valid combo |
| **Inventory** | Min stock to remove |
| **Compression** | Smallest encoding |
| **Routing** | Min cost path |

**Phone numbers** is canonical.

### Insight 8: Why Not Greedy "Find Min in Window"

> Some intuitions suggest "find smallest in window [0..k+1]".
> This is also valid (recursive variant), but stack is simpler and linear.

**Connection to:**
- **Alternative:** Recursive greedy.
- **Simpler:** Stack wins.

### Insight 9: Why Each Pop Removes One Digit

> Stack pop() removes one digit from the result.
> Decrement k to track remaining removals allowed.
> After loop, k=0 means we used all removals.

**Connection to:**
- **Counter:** k tracks budget.
- **Standard:** Decrement on action.

### Insight 10: Test Edge Cases First

> Edge cases that bite:
> - Empty result after removals: return "0".
> - All same digits: no pops, drop from end.
> - All increasing: same as above.
> - "10", k=1: pop '1' on '0', result "0".
> - Leading zeros: strip.

**Connection to:**
- **Robustness:** Always test edges.
- **Standard:** Defensive coding.

### Insight 11: Comparison to Largest Number (LC 414 variant)

> Different problem: arrange digits to form largest number.
> Here: remove digits to make smallest.
> Both use sort/greedy, but different mechanisms.

**Connection to:**
- **Related problems:** Family.
- **Different constraints:** Adapt code.

### Insight 12: Why Stack, Not Queue

> Stack gives LIFO: we want to compare recent digits (which we just added)
> to current. Queue would compare old digits.
> Stack is right because order matters (left-to-right scan).

**Connection to:**
- **Data structure:** Match operation.
- **Order:** LIFO vs FIFO.

### Insight 13: k Could Be 0 or n

> k=0: no removals, return num stripped.
> k=n: remove all, return "0".
> Both handled by base cases.

**Connection to:**
- **Boundary:** Always handle.
- **Standard:** Edge check.

### Insight 14: Stripping Can Be Done Via Index

> Instead of `lstrip("0")`, use index iteration:
> `i=0; while i < len(stack) and stack[i] == "0": i += 1`.
> Same result, slightly faster.

**Connection to:**
- **Optimization:** Avoid string allocation.
- **Standard:** Manual scan.

### Insight 15: Why This Is a "Greedy" Problem

> Local choice: pop bigger-before-smaller.
> Global optimum: smallest number overall.
> Greedy proof: removing big-before-small always reduces the number
> and never makes a later choice worse.

**Connection to:**
- **Greedy proof:** Standard.
- **Optimality:** Locally optimal.

---

## 🧪 TEST CASES

| `num` | `k` | Expected | Note |
|-------|-----|----------|------|
| `"1432219"` | 3 | `"1219"` | Standard |
| `"10200"` | 1 | `"200"` | Leading zero |
| `"10"` | 2 | `"0"` | Remove all |
| `"112"` | 1 | `"11"` | Duplicate digits |
| `"9"` | 1 | `"0"` | Single |
| `"1234567"` | 3 | `"1234"` | Increasing |
| `"1002001"` | 2 | `"1"` | Multiple zeros |
| `"112"` | 2 | `"1"` | Remove both leading |
| `"1234"` | 0 | `"1234"` | No removal |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Monotonic stack** | **O(n)** | **O(n)** | **✅ BEST** |
| Brute subsets | O(C(n,k)) | O(n) | ❌ Too slow |
| DP | O(n*k) | O(n*k) | ❌ Slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Smallest Subsequence (LC 1081) | Monotonic stack | https://leetcode.com/problems/smallest-subsequence-of-distinct-characters/ |
| Most Competitive Subseq (LC 1673) | Monotonic stack | https://leetcode.com/problems/find-the-most-competitive-subsequence/ |
| Create Max Number (LC 402-ish) | Monotonic stack | https://leetcode.com/problems/create-maximum-number/ |
| Largest Number At Least... | Sort | https://leetcode.com/problems/largest-number-at-least-twice-of-others/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Monotonic stack** = O(n) greedy for digit removal.
2. **"Big before small"** is always a removal.
3. **Strip leading zeros** at end.
4. **Drop last k** if k remains.
5. **Phone numbers** is canonical use case.
6. **Each digit pushed once, popped at most once.**
7. **Same skeleton** as LC 1081.
8. **Edge cases**: empty, all zeros, all same.
9. **Greedy = optimal** because local = global here.
10. **O(n) time, O(n) space** — optimal.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Phone numbers** | Min number |
| **Pricing** | Cheapest combo |
| **Inventory** | Min stock |
| **Compression** | Smallest encoding |
| **Routing** | Min cost path |
| **Trading** | Min transaction |
| **Scheduling** | Min completion time |
| **Sampling** | Min sample size |
| **Forecasting** | Min error |
| **Auction design** | Min reserve |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the monotonic stack greedy in 60 seconds
- [x] Can code the 7-line solution in 60 seconds
- [x] Know complexity: O(n) time, O(n) space
- [x] Know why "big before small" is optimal
- [x] Know how to handle k remaining at end
- [x] Know leading zero stripping
- [x] Know related problems (LC 1081, 1673)
- [x] Know amortized analysis (push once, pop at most once)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 7.
**Insight:** "Monotonic stack. Pop bigger digits when smaller comes. Drop last k if any remain. Strip leading zeros."