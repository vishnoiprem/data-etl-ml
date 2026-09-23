# Modified Binary Search — How to Think & How to Talk in Interviews

> "Modified Binary Search" is not one pattern. It's a family of problems where
> binary search is still the right tool, but the **monotonicity** lives in a
> non-obvious place (e.g., "the answer itself," not the input array).

This folder contains 10 curated problems that together span every flavor
of the pattern you'll meet at Meta / Google / Amazon.

---

## 1. The 30-second mental model

Plain binary search works because of **monotonicity**: if `arr[mid] < target`,
the target can only live to the right. Every Modified Binary Search variant
preserves that contract — you just have to **find the right monotonic predicate**.

Before writing any code, ask:

1. **What am I binary-searching over?**
   (an index `i`, a value `v`, a row in a matrix, a speed, a count...)
2. **What is the monotonic predicate `P(x)`?** (`True` on the left, `False` on the right, or vice versa)
3. **How do I compute `P(mid)` in O(1) or O(log n) using already-known info?**
4. **What is the search space `[lo, hi]` — inclusive or exclusive?**
5. **When the loop ends, what does `lo`/`hi` represent?** (the answer, the boundary, a "first True", a "last False"...)

If you can answer those five, you have a solution. If you can't answer #2,
you don't have a binary search — you have a linear scan.

---

## 2. The five shapes (use this to classify any prompt)

| # | Shape | Search over | Predicate | Hallmark problem |
|---|---|---|---|---|
| **A** | Index-based | an index in `arr` | `arr[i]` vs target | Search in Rotated Sorted Array |
| **B** | Boundary / "first or last" | an index | `arr[i] < target` vs `>=` | Find First and Last Position |
| **C** | Peak / neighbor-driven | an index | `arr[mid]` vs neighbor | Find Peak Element |
| **D** | BS on the answer | a *value* (rate, k, days) | "can we do it in `mid`?" | Koko Eating Bananas |
| **E** | BS + math formula | index, derived from formula | `f(i) >= target` | Kth Missing Positive, Reaching Points |

Whenever a problem says "smallest/largest value such that some condition holds,"
you're in shape **D** — the answer is not an array index.

---

## 3. The "Think Out Loud" framework for interviews

Interviewers score you on the **process**, not just the final `O(log n)`. Use
this script — adapted per problem, but the skeleton stays the same:

### Step 1 — Restate & classify (30 s)
> "So we have `<input>`. I want the `<answer>`. I think this is a **shape-D**
> binary search because we're looking for the smallest value of X such that
> a feasibility check passes. The naive approach would be `<O(n²) linear>`."

### Step 2 — Define the search space (30 s)
> "The answer is bounded between `<lo>` and `<hi>`. I can set `lo = <min
> possible>` and `hi = <max possible>`. I'll use an **inclusive** range
> because …"

### Step 3 — Define the monotonic predicate (45 s)
> "For a candidate `mid`, the question I want to ask is: *'can we finish
> the job in `mid`?'* If yes, the real answer is at most `mid`, so I move
> the high bound down. If no, I move the low bound up. This is monotonic
> because if we can do it in `mid`, we can also do it in any larger value."

### Step 4 — Write the loop, narrating (3 min)
> "Standard pattern: while `lo < hi`: compute `mid` (careful — I'll use
> `lo + (hi - lo) // 2` to avoid overflow in other languages), check the
> predicate, and move exactly one bound. The loop exits when `lo == hi`,
> which is the answer."

### Step 5 — Verify (1 min)
> "Edge cases: empty input, single element, target at the boundary, all
> duplicates. Let me trace through `<example>`."

### Step 6 — State complexity (15 s)
> "Time: `O(log(hi - lo) * cost(check))`. Space: `O(1)`."

---

## 4. Code template you'll reuse 90% of the time

```python
def search(lo, hi):
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if feasible(mid):
            hi = mid          # mid might be the answer, keep it
        else:
            lo = mid + 1      # mid is provably not the answer
    return lo                 # lo == hi == first feasible value
```

For "last feasible" problems, flip the moves:

```python
while lo < hi:
    mid = lo + (hi - lo + 1) // 2   # bias up
    if feasible(mid):
        lo = mid
    else:
        hi = mid - 1
return lo
```

For "exact-match in a rotated array" problems, you don't have a clean
predicate — you instead **discard half the array** based on which side is
sorted and whether the target lies in it.

---

## 5. How to handle the classic traps

| Trap | What to say | Fix |
|---|---|---|
| **Overflow in `mid`** | "I avoid `(lo+hi)//2` overflow." | `lo + (hi - lo) // 2` |
| **Infinite loop on `[lo, hi]`** | "If mid is always rounded down, `lo` may never advance." | For `lo = mid` branch, use `mid = lo + (hi - lo + 1) // 2` |
| **Empty input** | "If the input is empty, return `<sentinel>`." | Guard at top, not in the loop |
| **Duplicates break monotonicity** | "Plain BS won't work because `arr[lo] == arr[mid]` is ambiguous." | Shrink from the edges (`lo += 1`) — worst case degrades to O(n) |
| **Off-by-one in boundary** | "Do I want the first True or the last False?" | Draw the TTTF array before coding |
| **Forgetting the final return** | "When the loop ends, lo == hi." | Always return `lo` (or `hi`) |

---

## 6. The 10 problems in this folder

| # | File | Shape | Difficulty | One-line takeaway |
|---|---|---|---|---|
| 1 | `1_search_rotated_sorted_array.py` | A | Med | "Which half is sorted + is target inside it?" |
| 2 | `2_minimum_in_rotated_sorted_array_ii.py` | A | Hard | Duplicates: collapse, accept O(n) worst case |
| 3 | `3_search_a_2d_matrix.py` | A | Med | Flatten index → mid: `row = mid // n, col = mid % n` |
| 4 | `4_first_and_last_position.py` | B | Med | Two BS runs: lower_bound & upper_bound |
| 5 | `5_find_peak_element.py` | C | Med | If `arr[mid] > arr[mid+1]`, peak is to the left |
| 6 | `6_search_insert_position.py` | B | Easy | Canonical "first index where `arr[i] >= target`" |
| 7 | `7_koko_eating_bananas.py` | D | Med | BS on eating speed; predicate = "days needed ≤ H" |
| 8 | `8_find_k_closest_elements.py` | A/B | Med | BS on the **left boundary** of the window |
| 9 | `9_kth_missing_positive.py` | E | Med | `arr[i]` vs `i`; missing count = `arr[i] - i - 1` |
| 10 | `10_reaching_points.py` | E | Hard | Reverse-engineer: BS on number of subtractions |

---

## 7. Phrases that make you sound senior

- "The search space here is values, not indices, so this is binary search on the answer."
- "The predicate is monotonic because the feasibility function is monotone in `mid`."
- "I'll keep the bound inclusive so the loop invariant is `[lo, hi]` is still the candidate set."
- "The answer is the smallest `mid` such that `check(mid)` is true — classic lower_bound."
- "If duplicates exist, plain binary search degenerates; the worst case is O(n) but it's still correct."
- "This problem is essentially `bisect_left` / `bisect_right` from the standard library."
- "I'll dry-run on a 5-element example to validate my loop bounds before coding."

Use these. They signal you've seen the pattern before.

---

## 8. What to do when you're stuck in the interview

1. **State the brute force.** Don't hide it. "Brute force: scan everything in `O(n²)`."
2. **Identify the monotonic quantity.** "What changes monotonically as the candidate grows?"
3. **Try the smallest input.** n=1, n=2, n=3 — often reveals the predicate.
4. **Draw the TTTF (True-True-True-False-False) array.** If you can't draw it, it isn't BS.
5. **Ask: "Is there a formula `f(i)` that's monotone in `i`?"** If yes → shape E.
6. **Code the template, then adapt.** Don't try to be clever — the template works.

---

## 9. Recommended drill order

1. `6_search_insert_position` — pure template, build muscle memory.
2. `4_first_and_last_position` — same template, twice.
3. `9_kth_missing_positive` — introduce the math flavor.
4. `5_find_peak_element` — learn to discard using neighbors.
5. `1_search_rotated_sorted_array` — discard using which side is sorted.
6. `3_search_a_2d_matrix` — index mapping.
7. `7_koko_eating_bananas` — BS on the answer, the most important pattern.
8. `8_find_k_closest_elements` — BS where the answer is a window, not a point.
9. `2_minimum_in_rotated_sorted_array_ii` — handle duplicates honestly.
10. `10_reaching_points` — BS combined with number theory; the hardest.

After #7, you should be able to solve most "Modified Binary Search" problems
in under 25 minutes.
