# Subsets / Perms / Combos — Interview Playbook

> This is the document that turns these 8 problems from "memorised answers" into a system you can apply to ANY new problem the interviewer throws at you.

---

## 0. Mental model (say this out loud every interview)

> "There are **2ⁿ subsets of an n-element set**, because every element is **independently in or out**. The whole folder is just different ways of *generating*, *restricting*, or *re-ordering* those subsets."

That's it. Say it once near the start of the interview and the room visibly relaxes.

---

## 1. The 3 questions you ask the problem first

Before writing a single line, ask the interviewer (or yourself):

| # | Question | What it decides |
|---|----------|-----------------|
| Q1 | Is **order** important? | Order matters → permutation. Order ignored → subset/combination. |
| Q2 | Can elements **repeat**? | No → standard recursion. Yes → sort + skip-equal-to-previous. |
| Q3 | Are there **constraints** (size k, sum, validity, count)? | Add a **prune** clause at the top of the recursion. |

This 3-question template works for ~80% of backtracking problems, full stop.

---

## 2. The universal backtracking skeleton

Memorise this once. Every file in this folder is a tiny variation of it.

```python
def solve(input):
    res, path = [], []

    def dfs(start_or_state):        # "start" for subsets, state for perm
        if IS_COMPLETE(path):
            res.append(path.copy())
            return
        for CHOICE in available_choices(start_or_state):
            if INVALID(CHOICE, path):      # ← prune early
                continue
            MAKE(CHOICE)                   # push / mark used / decrement counter
            dfs(UPDATE(start_or_state))
            UNMAKE(CHOICE)                 # pop / unmark / restore
    dfs(INITIAL)
    return res
```

Three knobs change between problems:
1. **`IS_COMPLETE`** – empty for subsets ("record every node"), `len==k` for size-restricted, etc.
2. **`CHOICE` loop bounds** – `range(i+1, n)` → subset. `range(0, n)` skipping `used` → permutation.
3. **`INVALID`** – duplicate-skip, validity (parentheses), insufficient remaining elements.

---

## 3. Decision matrix for the 8 problems

| File | Order? | Duplicates? | Restriction | Memory hook |
|------|--------|-------------|-------------|--------------|
| `01_introduction_to_subsets.py`   | ❌ | ❌ | none | Record at **every node** of the tree. |
| `02_find_k_sum_subsets.py`       | ❌ | ❌ | size=k AND sum=target | Add two prune lines: `len<k`, `sum<=target`. |
| `03_subsets.py`                  | ❌ | ❌ | none | The "produce-at-each-node" template. |
| `04_permutations.py`             | ✅ | ❌ | use all | `start=0` + `used[]` array OR swap-in-place. |
| `05_letter_combinations_phone_number.py` | ✅ | n/a | product of digit options | "Cartesian product" feel. |
| `06_generate_parentheses.py`     | ✅ | n/a | always valid prefix | Two prune lines: `( < n` and `) < (`. |
| `07_letter_case_permutation.py`  | ✅ | n/a | letter → 2 choices, digit → 1 | Mix-and-match single/multi branches. |
| `08_letter_tile_possibilities.py`| ✅ | ✅ | unique seqs only | Use a `Counter` instead of `used[]` and update in place. |
| `09_subsets_ii.py`               | ❌ | ✅ | no duplicate subsets | **Sort + skip `nums[i]==nums[i-1]` when `i>start`.** |

---

## 4. How to talk in the interview (script)

When you open the problem, say ONE sentence per phase:

1. **Restate** (5 s):
   > "So we want every X we can build from Y under constraint Z. There are at most N possibilities because …"

2. **Classify** (10 s):
   > "Order matters / doesn't matter, duplicates possible / not, so I think this is a **subset / permutation / Cartesian-product** problem."

3. **Sketch** (30 s):
   > "I'll do a backtracking DFS. At each index I'll decide include/skip (or pick any unused letter), and I'll prune when …"

4. **Code** (~5 min) — narrate the three knobs from §2:
   > "Here's the base case, here's the prune, here's the for-loop with make/unmake."

5. **Test by hand** (1 min):
   > "Let me walk through n=2: we recurse here, record this, backtrack …"

6. **Complexity** (30 s):
   > "There are N leaves, each takes O(k) to copy, so time O(N·k), space O(N) for the recursion stack plus output."

---

## 5. Traps & how to dodge them

| Trap | Symptom | Fix |
|------|---------|-----|
| Forgetting `path.copy()` | All subsets end up identical (empty or last value) | Always `.copy()` / `.append(slice)`. |
| Mutating `used[]` but never resetting | Interviewee traces your code and it diverges | Mirror every `used[i]=True` with `used[i]=False`. |
| Off-by-one in duplicate skip (`i>start` vs `i>0`) | Wrong answer on `[1,1,2]` | Skip **only at the same recursion depth**: `i > start`. |
| Trying to dedupe permutations with a `seen` set | Misses valid permutations or gives TLE | Use a `Counter` approach (problem 08) or skip-by-prev after sorting. |
| Forgetting early prune | TLE on inputs > 15 | Always check the smallest valid possibility before recursing. |

---

## 6. Order in which to re-derive from scratch

If you blank out in the interview, derive in this order — they build:

```
01 subsets         ─► 03 subsets          (same algo, clean writeup)
        │
        ├──► 02 k-sum subsets         (add len + sum prune)
        └──► 09 subsets II           (add sort + skip dup)

04 permutations    ─► 08 letter tiles     (Counter permutation)
05 phone keypad    ─► 07 case perm        (mixed-arity Cartesian)
06 parentheses     ── standalone, just practice the prune
```

Memorise the two endpoints (subsets, permutations); everything else is "subsets + one prune" or "permutations + one prune".

---

## 7. Cheat-sheet one-pager

```
SUBSETS / COMBOS          PERMUTATIONS
for j in range(start,n):  for j in range(0,n):
    if SKIP_DUP: continue     if used[j]: continue
    push                      push; mark used
    dfs(j+1)                  dfs()
    pop                       pop;  unmark
```

Add a prune clause at the top of the function, and a "record at every node / record at leaf" choice — done.

---

## 8. After the interview (review log)

For each problem you got wrong, write:
1. **What did I classify wrong?** (order / duplicates / constraints)
2. **What prune was I missing?**
3. **What's the smallest failing test?**

Do this 3 times and you'll classify any new problem in <30 seconds during the real interview.
