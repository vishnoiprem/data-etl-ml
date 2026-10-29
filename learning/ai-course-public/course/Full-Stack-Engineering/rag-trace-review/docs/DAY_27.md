# Day 27 — Algorithms: Arrays, Strings, and Hash Maps
**Module 21** | Total: 90 min (10 + 20 + 30 + 20 + 20)

> **Read first:** `docs/ALGORITHMS_PRIMER.md` for the 60-min framework, Big-O cheat sheet, and the 50 most-asked problems list.

---

## 1. Simple explanation (10 min)

Most "interview" problems are really **array problems with a twist**. The patterns are:
1. **Hash map for O(1) lookup** — turn an O(n²) "find a match" into O(n).
2. **Sort first** — most array problems become easier on sorted input.
3. **Two pointers** — sweep from both ends; one pass instead of nested loops.

If you know these three, you can solve ~40% of FAANG interview problems.

---

## 2. Technical concepts (20 min)

### When to use a hash map
- "Find if X exists" → `set`.
- "Count frequencies" → `dict`.
- "Two-sum / complement lookup" → `dict[value] = index`.
- Tradeoff: O(n) extra space, but O(1) lookup.

### When NOT to use a hash map
- You need order: use a sorted array or a `deque`.
- You need range queries: use a Fenwick tree or segment tree.
- You need the k-th largest/smallest: use a heap.

### Sorting as a superpower
- Many "find pair" / "find triplet" problems want you to sort first.
- Sort + two pointers = O(n log n + n) = O(n log n).
- Sort + sweep = O(n log n).
- Sort + greedy = O(n log n) (intervals).

### Sliding window (preview)
- Window `[l, r]` expands right, shrinks left.
- O(n) total because each index is visited at most twice.
- Used for subarray/substring with a constraint.

### Complexity ladder
| Operation | Naive | With hash | With sort |
|---|---|---|---|
| Find pair | O(n²) | O(n) | O(n log n) |
| Find unique | O(n²) | O(n) | O(n) |
| Top K | O(n log n) | O(n) with Counter + heap | O(n log n) with sort |
| Subarray sum | O(n²) | O(n) prefix+map | O(n log n) |

---

## 3. Coding (30 min)

Solve **3 problems**, each in ~10 min.

### Problem 1: Two Sum

Given an array `nums` and a `target`, return indices of the two numbers that add up to `target`. Each input has exactly one solution; you can't use the same index twice.

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}  # value -> index
    for i, v in enumerate(nums):
        need = target - v
        if need in seen:
            return [seen[need], i]
        seen[v] = i
    return [-1, -1]
```

- **Time:** O(n). **Space:** O(n).
- **Sample:** `[2,7,11,15], 9` → `[0,1]`.

### Problem 2: Group Anagrams

Given a list of strings, group the anagrams together.

```python
from collections import defaultdict

def group_anagrams(strs: list[str]) -> list[list[str]]:
    groups: dict[tuple, list[str]] = defaultdict(list)
    for s in strs:
        # Sorted string is the canonical key
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())
```

- **Time:** O(n · k log k) where k = avg length. Sorting dominates.
- **Alternative key:** `tuple(Counter(s).items())` — same complexity, different style.
- **Sample:** `["eat","tea","tan","ate","nat","bat"]` → `[["bat"],["nat","tan"],["ate","eat","tea"]]`.

### Problem 3: Top K Frequent Elements

Given a list and k, return the k most frequent elements.

```python
from collections import Counter
import heapq

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)                       # O(n)
    # Heap keeps smallest of the top-k; size bounded by k
    return heapq.nlargest(k, counts.keys(), key=counts.get)
```

- **Time:** O(n log k). **Space:** O(n).
- **Sample:** `[1,1,1,2,2,3], 2` → `[1,2]`.
- **Alternative:** bucket sort by frequency for O(n) time, O(n) space.

---

## 4. Debugging & tests (20 min)

### Bug 1: two_sum uses the same element twice
**Symptom:** A naive version with `if v in seen: return [seen[v], i]` works for distinct values, but for `nums = [3,3]`, target = 6 it returns `[0, 1]` (correct). However, a version that doesn't check `need in seen` BEFORE inserting current can match the wrong pair.
**Fix:** always check `need in seen` before writing to `seen[v] = i`. Order matters.

### Bug 2: group_anagrams mutates the dict key
**Symptom:** later, the groups are wrong because keys changed.
**Fix:** convert to immutable: `tuple(sorted(s))`. Lists aren't hashable.

### Bug 3: top_k_frequent tie broken wrong
**Symptom:** with `k=1` and `[1,2]` both have freq 1; which wins?
**Fix:** `heapq.nlargest` is stable; documented behavior. Mention in interview.

### Bug 4: never tested empty input
**Fix:** add `[]` test case. Two_sum returns `[-1,-1]`. Group_anagrams returns `[]`. Top_k returns `[]`.

### Tests
```python
def test_two_sum():
    assert sorted(two_sum([2,7,11,15], 9)) == [0, 1]
    assert two_sum([3,3], 6) == [0, 1]  # same value, distinct indices

def test_group_anagrams():
    g = group_anagrams(["eat","tea","tan","ate","nat","bat"])
    # normalize before compare
    assert sorted([sorted(x) for x in g]) == [["ate","eat","tea"], ["bat"], ["nat","tan"]]

def test_top_k():
    assert sorted(top_k_frequent([1,1,1,2,2,3], 2)) == [1, 2]
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Why use a hash map instead of two loops?"**
> Two loops is O(n²). Hash map gives O(1) lookup → O(n) total.

**Q2 — "What's the space vs time tradeoff?"**
> Hash map uses O(n) space to save O(n) time. When n is small, the brute force might be faster (cache friendliness).

**Q3 — "How do you sort by value, not key?"**
> Use `sorted(items, key=lambda kv: kv[1])`. Or a Counter + `heapq.nlargest`.

**Q4 — "Two Sum II (sorted) — same problem, sorted input. Different solution?"**
> Yes — use two pointers. `l=0, r=n-1`. Move l/r based on sum. O(1) extra space.

**Q5 — "How do you handle streaming data with Top K?"**
> Maintain a Count-Min Sketch + heap with size k. O(1) amortized insert.

---

## 6. Success criteria check
- [ ] I can solve Two Sum with a hash map in < 5 min.
- [ ] I can identify when to sort first.
- [ ] I can name 3 tradeoffs of hashing.
- [ ] I can write all 3 problems from memory.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/60** |

(Pass mark: ≥42/60 = 70%. Distinction: ≥48/60.)

## 8. Coding assignment
**Product of Array Except Self** — given `nums`, return an array `ans` where `ans[i]` = product of all `nums[j]` for `j != i`. No division. O(n) time.

### Rubric (0–10)
- 0: doesn't compile
- 4: returns same array (forgot prefix/suffix)
- 6: O(n) with prefix + suffix arrays
- 8: O(1) extra space (reuse output)
- 10: handles zeros correctly

### Solution
```python
def product_except_self(nums: list[int]) -> list[int]:
    n = len(nums)
    ans = [1] * n
    # prefix
    p = 1
    for i in range(n):
        ans[i] = p
        p *= nums[i]
    # suffix
    s = 1
    for i in range(n - 1, -1, -1):
        ans[i] *= s
        s *= nums[i]
    return ans
```

**Time: 90 min**
