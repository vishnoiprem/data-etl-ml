# Python Solutions — Easy → Hard thinking ladder

Companion to the 10 `.py` files in this folder.

For each problem we give:
- **L0 – Easy / brute force** (the first thing that comes to mind, O(n²) or worse).
- **L1 – Medium / interview-canonical** (the solution already in the `.py` file).
- **L2 – Hard / production-grade** (the variant that scales, handles edge cases, or uses a richer data structure).
- **How to think** — a short script you can say out loud at each level so you climb the ladder deliberately instead of jumping to the "clever" answer.

> Rule of thumb: **state L0 first in the interview, then say "I can do better — here's L1," then optionally "and here's L2 if the constraints demand it."** It signals range without showing off.

---

## How to think, in general

1. **Restate the problem in one sentence.** "Given X, return Y, where Y is the max/min/count/rank of something." If you can't say it in one sentence, you don't understand the problem.
2. **Brute-force it (L0).** What's the dumbest code that works? Nested loops, list comprehensions, `in` checks. Get an answer on the board — even if it's O(n²).
3. **Identify the bottleneck.** What's being repeated? Is it comparisons, lookups, or traversal?
4. **Pick the right tool.**
   - Repeated lookups → `dict` or `set` (O(1) amortized).
   - Top-K → `heapq.nlargest` / `nsmallest`, or sort once.
   - Sorted input → two pointers, binary search.
   - Streaming events → heap, sweep line.
5. **Write L1 cleanly.** One pass if possible. Single responsibility per loop.
6. **Only then reach for L2.** Heaps, segment trees, sliding windows, sweeps. L2 is justified only when (a) the interviewer asked, (b) the input size is huge, or (c) L1 has a real bug under edge cases.

---

## Problem 1 — Average book price  *(1_average_book_price.py)*

**L0 – Easy / brute force**
```python
def average_price(prices):
    total = 0
    count = 0
    for p in prices:
        total += p
        count += 1
    return total / count if count else 0
```
**How to think:** "Loop through and accumulate sum + count. The only edge case is empty."

**L1 – Medium / interview-canonical** *(in `.py` file)*
```python
return sum(prices) / len(prices) if prices else 0.0
```
**How to think:** "Python's `sum` + `len` is the built-in answer. Two lines, O(n)."

**L2 – Hard / streaming or numerical**
```python
import statistics
return statistics.fmean(prices) if prices else 0.0   # numerically stable; accepts iterators
```
**How to think:** "`fmean` is faster than `sum/len` for huge lists and handles precision better. Mention it if the interviewer pushes on numerical stability or on 'what if this is a generator, not a list?'"

---

## Problem 2 — Most common comment across locations  *(2_most_common_comment.py)*

**L0 – Easy / brute force**
```python
def most_common_comment(comments_by_location):
    best, best_count = '', 0
    for loc in comments_by_location:
        unique = set(loc)
        for c in unique:
            n = sum(1 for other in comments_by_location if c in other)
            if n > best_count:
                best, best_count = c, n
    return best
```
**How to think:** "For every comment, count how many distinct locations contain it. Nested loops → O(L²·K). Ugly but correct."

**L1 – Medium / dict** *(in `.py` file)*
```python
counts = {}
for loc in comments_by_location:
    for c in set(loc):
        counts[c] = counts.get(c, 0) + 1
return max(counts, key=counts.get) if counts else ''
```
**How to think:** "One pass: dedup inside each location with `set(loc)`, increment a dict. `max(..., key=...)` picks the winner. O(L·K)."

**L2 – Hard / Counter + tie-breaks**
```python
from collections import Counter
flat = Counter(c for loc in comments_by_location for c in set(loc))
# Tie-break alphabetically:
return min(flat.most_common(), key=lambda kv: (-kv[1], kv[0]))[0] if flat else ''
```
**How to think:** "`Counter.most_common()` already sorts by count desc. To break ties alphabetically, sort on `(-count, name)`. If ties don't matter, just take `most_common(1)`."

---

## Problem 3 — Max unique books within a budget  *(3_max_books_within_budget.py)*

**L0 – Easy / brute force**  Try every subset, take the cheapest.
```python
from itertools import combinations
def max_unique_books(prices, budget):
    best = 0
    for r in range(1, len(prices) + 1):
        for combo in combinations(prices, r):
            if sum(combo) <= budget:
                best = max(best, r)
    return best
```
**How to think:** "All subsets — O(2ⁿ·n). Fine for n≤20; useless otherwise."

**L1 – Medium / greedy sort** *(in `.py` file)*
```python
prices_sorted = sorted(prices)
spent = count = 0
for p in prices_sorted:
    if spent + p > budget: break
    spent += p; count += 1
return count
```
**How to think:** "Greedy: buy cheapest first. Optimal because each cheap book frees budget. O(n log n)."

**L2 – Hard / heap or DP**
```python
# heap alternative — same complexity but constant extra space beyond the input
import heapq
return sum(p for p in heapq.nsmallest(len(prices), prices) if (spent := spent + p) <= budget)  # pseudocode

# DP variant (when books have copies or k must equal exactly some target):
# dp[w] = max books achievable with budget w
```
**How to think:** "The heap is the same algorithm; sorting is just clearer. DP only matters if the problem adds 'exactly k books' or 'unlimited copies'."

---

## Problem 4 — Max concurrent meeting attendees  *(4_max_concurrent_meeting_attendees.py)*

**L0 – Easy / pairwise check**
```python
def max_attendees(meetings):
    best = 0
    for t in range(min(m.start for m in meetings), max(m.end for m in meetings) + 1):
        s = sum(m.people for m in meetings if m.start <= t < m.end)
        best = max(best, s)
    return best
```
**How to think:** "Check every instant. O(n·range). Fine for tiny inputs."

**L1 – Medium / sweep line** *(in `.py` file)*
```python
events = []
for m in meetings:
    events.append((m.start, +m.people))
    events.append((m.end, -m.people))
events.sort(key=lambda e: (e[0], e[1]))   # ends before starts on tie
running = best = 0
for _, d in events: running += d; best = max(best, running)
return best
```
**How to think:** "Two events per meeting, sort, sweep. End events first on tie — that's the classic bug to call out."

**L2 – Hard / segment tree or streaming**
```python
# Segment tree for range-add / point-max if meetings are dense and times are bounded.
# Streaming: SortedList of end times — add on start, remove on end, peak = answer.
from sortedcontainers import SortedList
active = SortedList()
peak = 0
for m in sorted(meetings, key=lambda m: m.start):
    active.add((m.end, m.people))
    # remove meetings that have ended
    while active and active[0][0] <= m.start:
        active.pop(0)
    peak = max(peak, sum(p for _, p in active))
return peak
```
**How to think:** "Streaming version is `SortedList` keyed by end time. Mention only if data arrives in real time."

---

## Problem 5 — Max classes across consecutive years  *(5_consecutive_years_workshops.py)*

**L0 – Easy / nested loops**
```python
def max_classes_consecutive_years(workshops):
    best = 0
    for i, (y1, _) in enumerate(workshops):
        run = 0
        for y2, n in workshops[i:]:
            if y2 - y1 > 1: break
            run += n
        best = max(best, run)
    return best
```
**How to think:** "For each starting year, sum until the gap exceeds 1. O(n²)."

**L1 – Medium / aggregate + single pass** *(in `.py` file)*
```python
by_year = {}
for y, n in workshops: by_year[y] = by_year.get(y, 0) + n
best = run = 0
prev = None
for y in sorted(by_year):
    run = by_year[y] if prev is None or y - prev > 1 else run + by_year[y]
    best = max(best, run); prev = y
return best
```
**How to think:** "Aggregate first (handles duplicates), sort, walk. O(n log n)."

**L2 – Hard / sweep on year-axis**
```python
# When year range is bounded (say 1900..2100), use a difference array on a year-axis:
lo, hi = min(y for y,_ in workshops), max(y for y,_ in workshops)
arr = [0]*(hi-lo+2)
for y, n in workshops:
    arr[y-lo] += n
run = best = 0
for v in arr:
    run = v if v else 0
    best = max(best, run)
return best
```
**How to think:** "Bounded years → O(Y) sweep on the year axis. Reset `run` when a year has zero workshops."

---

## Problem 6 — Smallest number from odd digits  *(6_smallest_from_odd_digits.py)*

**L0 – Easy / build list, sort**
```python
def smallest_from_odd_digits(n):
    odd = [int(d) for d in str(n) if int(d) % 2 == 1]
    odd.sort()
    return int(''.join(map(str, odd))) if odd else 0
```
**How to think:** "Extract, sort ascending, join."

**L1 – Medium / `sorted` directly on string** *(in `.py` file)*
```python
odd_digits = sorted(d for d in str(abs(n)) if int(d) % 2 == 1)
return int(''.join(odd_digits)) if odd_digits else 0
```
**How to think:** "`sorted` works on strings. `abs()` handles negatives."

**L2 – Hard / counting sort**
```python
# Digits are 0..9 — use a count array, no need to sort:
counts = [0]*10
for d in str(abs(n)):
    if int(d) % 2 == 1: counts[int(d)] += 1
result = ''.join(str(d)*counts[d] for d in (1,3,5,7,9) for _ in range(counts[d]))
return int(result) if result else 0
```
**How to think:** "Counting sort is O(d) instead of O(d log d). Tiny win; mention only if asked about algorithmic lower bounds."

---

## Problem 7 — Most-mentioned word across categories  *(7_most_mentioned_word.py)*

**L0 – Easy / nested loops**
```python
def most_mentioned(d):
    counts = {}
    for words in d.values():
        for w in words:
            counts[w] = counts.get(w, 0) + 1
    if not counts: return ('', 0)
    best = max(counts, key=counts.get)
    return best, counts[best]
```
**How to think:** "Two nested loops, dict accumulator, `max`."

**L1 – Medium / `Counter`** *(in `.py` file)*
```python
from collections import Counter
c = Counter()
for words in d.values(): c.update(words)
return c.most_common(1)[0] if c else ('', 0)
```
**How to think:** "`Counter` is the standard tool. `update` merges another iterable's counts."

**L2 – Hard / Top-N + streaming**
```python
import heapq
counter = Counter(w for words in d.values() for w in words)
top_n = heapq.nlargest(10, counter.items(), key=lambda kv: kv[1])   # returns [(word, count), ...]
# Or streaming: keep a heap of size k as you process.
```
**How to think:** "If you need Top-K instead of just the max, switch to `nlargest`. If the input is a stream and memory matters, use a bounded heap."

---

## Problem 8 — Search an unsorted list  *(8_search_unsorted_list.py)*

**L0 – Easy / `.index()`** *(in `.py` file)*
```python
def search(lst, target):
    try: return lst.index(target)
    except ValueError: return -1
```
**How to think:** "`list.index` is built-in; O(n), returns -1 on miss via try/except."

**L1 – Medium / explicit loop**
```python
for i, x in enumerate(lst):
    if x == target: return i
return -1
```
**How to think:** "Same complexity, but readable. Use this in interviews — `.index` looks too easy."

**L2 – Hard / many queries on a static list**
```python
index_map = {x: i for i, x in enumerate(lst)}    # O(n) build, O(1) lookup
return index_map.get(target, -1)
```
**How to think:** "If the list is searched many times, build a `{value: index}` dict once. Trade memory for time."

---

## Problem 9 — Largest number from digits  *(9_largest_number_from_digits.py)*

**L0 – Easy / sort descending** *(in `.py` file)*
```python
return int(''.join(sorted(str(n), reverse=True))) if n else 0
```
**How to think:** "Sort digits descending, join, convert back."

**L1 – Medium / handle zero & negative**
```python
if n == 0: return 0
digits_desc = sorted(str(abs(n)), reverse=True)
return int(''.join(digits_desc))
```
**How to think:** "`abs()` for negatives; explicit zero check avoids the `'0' → 0` ambiguity."

**L2 – Hard / counting sort + leading-zero edge case**
```python
# Counting sort — O(d), no comparison sort.
counts = [0]*10
for d in str(abs(n)): counts[int(d)] += 1
result = ''.join(str(d)*counts[d] for d in range(9, -1, -1))
return int(result) if result else 0
```
**How to think:** "Counting sort beats `sorted` for tiny alphabets. Useful when the digit count is huge."

---

## Problem 10 — Max overlapping meetings  *(10_max_overlapping_meetings.py)*

**L0 – Easy / pairwise check**
```python
def max_overlapping(meetings):
    best = 0
    for s1, e1 in meetings:
        c = sum(1 for s2, e2 in meetings if s2 < e1 and s1 < e2)
        best = max(best, c)
    return best
```
**How to think:** "For each meeting, count overlaps. O(n²)."

**L1 – Medium / sweep line** *(in `.py` file)*
```python
events = []
for s, e in meetings:
    events.append((s, +1)); events.append((e, -1))
events.sort(key=lambda e: (e[0], e[1]))   # ends first on tie
return max(itertools.accumulate(d for _, d in events))  # or manual loop
```
**How to think:** "Two events per meeting, sweep. The 'end before start on tie' rule is the bug to call out loud."

**L2 – Hard / min-heap (LeetCode-canonical)**
```python
import heapq
ends = []
for s, e in sorted(meetings):
    while ends and ends[0] <= s: heapq.heappop(ends)
    heapq.heappush(ends, e)
return max(len(ends), ...)   # peak heap size during the walk
```
**How to think:** "Sort by start, keep a heap of active end times, pop expired meetings. Heap size = rooms needed. Same complexity, more explicit 'active meetings' set."

---

## Cheat-sheet — when to reach for what

| Symptom in the problem | Reach for |
|---|---|
| "most frequent", "count duplicates" | `Counter` / dict |
| "top K" | `heapq.nlargest` |
| "is X present, repeatedly" | `set` |
| "input sorted" | two pointers / binary search |
| "intervals / meetings / overlaps" | sweep line OR min-heap |
| "consecutive run" | aggregate then single pass |
| "stream of events" | heap + lazy deletion |
| "max sum of k subarray" | sliding window |
| "smallest / largest by rearrangement" | sort by the right key |
| "all subsets" | backtracking; otherwise DP |

## Interview macro

When you hear the prompt:
1. Repeat it in one sentence.
2. Say **L0**: "Brute force: …" — write it.
3. Say **why it sucks**: "That's O(n²) because of nested loops."
4. Say **L1**: "Better: I'll keep a dict / sort once / sweep — O(n log n)."
5. Write L1 cleanly.
6. (If asked) **L2**: "For streaming / huge input / extra constraints, here's the heap / tree / DP variant."
7. State **complexity** and the **edge cases** you handled.

That's how you climb easy → medium → hard in the room without sounding like you're winging it.
