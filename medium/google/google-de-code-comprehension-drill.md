# Code Comprehension Drill — "Output? Complexity? How to Improve?"

> This is the EXACT format reported for the Google Cloud/Data Engineer technical screen: you're shown a program and asked **(1) what is the output, (2) what is the time complexity, (3) how can it be improved?**
>
> How to use: cover the ANSWER block, work each problem aloud as if the interviewer is listening (predict output → state Big-O → propose improvement → state new Big-O), then check yourself. Verbalizing is half the score.

---

## PROBLEM 1
```python
def find_dupes(nums):
    dupes = []
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j] and nums[i] not in dupes:
                dupes.append(nums[i])
    return dupes

print(find_dupes([1, 2, 3, 2, 4, 1]))
```
**ANSWER**
- **Output:** `[1, 2]` — wait, trace it: i=0 (1) matches j=5 (1) → append 1; i=1 (2) matches j=3 (2) → append 2. So `[1, 2]`.
- **Time complexity:** O(n²) from the nested loops, and `nums[i] not in dupes` is another O(n) scan → worst case O(n³)-ish. Say "O(n²) dominated, with a hidden linear membership check."
- **Improve:** use a set to track seen values in one pass.
```python
def find_dupes(nums):
    seen, dupes = set(), set()
    for x in nums:
        if x in seen:
            dupes.add(x)
        seen.add(x)
    return list(dupes)
```
**New complexity:** O(n) time, O(n) space. *Talking point:* set membership is O(1) average vs O(n) for a list — the core insight they're testing.

---

## PROBLEM 2
```python
def build_string(words):
    s = ""
    for w in words:
        s = s + w + ","
    return s

print(build_string(["a", "b", "c"]))
```
**ANSWER**
- **Output:** `"a,b,c,"` (trailing comma).
- **Time complexity:** O(n²). Strings are immutable in Python, so each `s = s + w` builds a brand-new string copying all previous characters.
- **Improve:** accumulate in a list and `join` once.
```python
def build_string(words):
    return ",".join(words) + ("," if words else "")
```
**New complexity:** O(n). *Talking point:* immutability of strings is the trap; `join` allocates once.

---

## PROBLEM 3
```python
def second_largest(nums):
    nums.sort(reverse=True)
    return nums[1]

print(second_largest([5, 1, 9, 3]))
```
**ANSWER**
- **Output:** `5` (sorted desc: 9,5,3,1 → index 1 = 5).
- **Time complexity:** O(n log n) from the sort.
- **Improve:** single pass tracking top two → O(n). Also flag bugs: crashes on lists shorter than 2, and mutates the caller's list.
```python
def second_largest(nums):
    if len(nums) < 2:
        raise ValueError("need at least two elements")
    first = second = float('-inf')
    for x in nums:
        if x > first:
            first, second = x, first
        elif x > second and x != first:
            second = x
    return second
```
**New complexity:** O(n) time, O(1) space. *Talking point:* you don't need a full sort to find the 2nd largest — and calling out the mutation + edge case shows seniority.

---

## PROBLEM 4 (output-trap / comprehension focus)
```python
def add_item(item, items=[]):
    items.append(item)
    return items

print(add_item(1))
print(add_item(2))
print(add_item(3))
```
**ANSWER**
- **Output:**
  ```
  [1]
  [1, 2]
  [1, 2, 3]
  ```
- **Why:** the **mutable default argument** is created ONCE at function definition and shared across all calls. This is the single most-loved Python comprehension trap.
- **Improve / fix:**
```python
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```
**Talking point:** "Default arguments are evaluated once at def time, not per call." Saying that sentence alone scores the point.

---

## PROBLEM 5
```python
def count_words(text):
    counts = {}
    for word in text.split():
        if word in counts:
            counts[word] = counts[word] + 1
        else:
            counts[word] = 1
    return counts

print(count_words("the cat the dog the bird"))
```
**ANSWER**
- **Output:** `{'the': 3, 'cat': 1, 'dog': 1, 'bird': 1}`
- **Time complexity:** O(n) in the number of words — this one is already efficient.
- **Improve (readability, not Big-O):** use `collections.Counter` or `dict.get`.
```python
from collections import Counter
def count_words(text):
    return dict(Counter(text.split()))
```
**Talking point:** when the complexity is already optimal, say so honestly and offer a *readability/idiomatic* improvement instead of inventing a fake speedup. Interviewers respect that.

---

## PROBLEM 6
```python
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(10))
```
**ANSWER**
- **Output:** `55`.
- **Time complexity:** O(2ⁿ) — exponential, because the same subproblems are recomputed in two branches.
- **Improve:** memoize → O(n), or iterate with O(1) space.
```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```
**New complexity:** O(n) time, O(1) space. *Talking point:* recursion tree has overlapping subproblems → classic memoization / bottom-up DP.

---

## PROBLEM 7
```python
def has_pair_sum(nums, target):
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j and nums[i] + nums[j] == target:
                return True
    return False

print(has_pair_sum([2, 7, 11, 15], 9))
```
**ANSWER**
- **Output:** `True` (2 + 7 = 9).
- **Time complexity:** O(n²); also note the inner loop starts at 0, so each pair is checked twice — wasteful.
- **Improve:** one pass with a set of complements.
```python
def has_pair_sum(nums, target):
    seen = set()
    for x in nums:
        if target - x in seen:
            return True
        seen.add(x)
    return False
```
**New complexity:** O(n) time, O(n) space. *Talking point:* trading space for time with a hashset — the most common DE optimization pattern.

---

## PROBLEM 8
```python
def dedupe_preserve_order(items):
    result = []
    for x in items:
        if x not in result:
            result.append(x)
    return result

print(dedupe_preserve_order([3, 1, 3, 2, 1, 4]))
```
**ANSWER**
- **Output:** `[3, 1, 2, 4]`.
- **Time complexity:** O(n²) — `x not in result` scans the growing list each time.
- **Improve:** track membership in a set; or in modern Python, `dict.fromkeys` preserves order.
```python
def dedupe_preserve_order(items):
    seen, result = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result
# or simply:  return list(dict.fromkeys(items))
```
**New complexity:** O(n). *Talking point:* same set-vs-list membership insight as Problem 1 — they recur because they're the heart of the format.

---

## THE 4-STEP SCRIPT TO SAY OUT LOUD FOR EVERY ONE
1. **"Let me trace it with the given input..."** — narrate state changes, give the output.
2. **"The complexity is O(___) because..."** — name the dominant operation and *why* (nested loop, immutable copy, membership scan, recomputation).
3. **"I can improve this by..."** — name the data structure or technique, then write it.
4. **"That brings it to O(___) time and O(___) space."** — always close with the new bound.

## THE RECURRING INSIGHTS (almost every "improve" answer is one of these)
- List membership `in` is O(n) → use a **set/dict** for O(1).
- String building in a loop is O(n²) → **join**.
- Sorting to find a few extremes is O(n log n) → **single pass** O(n).
- Recomputed subproblems are exponential → **memoize / bottom-up DP**.
- Nested-loop pair search is O(n²) → **hashset of complements** O(n).
- Trade **space for time** with a hashmap — the default DE move.

## ALSO PREPARE (from the same transcript, in case the screen wanders)
- Data concepts: data warehousing, OLAP vs OLTP, data modeling, SQL vs NoSQL.
- Cloud: services of whatever cloud you've used (GCP fine to lean on; BigQuery, Dataflow, Pub/Sub, Cloud Storage).
- Big-data frameworks: Hadoop, Spark — and one line on *how/why* each works.
