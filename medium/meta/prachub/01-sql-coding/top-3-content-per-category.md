# Return Top-3 Content per Category

## 1. Simple way to think
- Input: a list of `(content_id, category, rating)` tuples.
- Output: for every category, the top-k (default 3) items by rating (ties broken by content_id).
- Mental model: sort each "category bucket" independently, then take the first k.
- The function should be pure (no mutation of input), handle ties, and handle an empty input.

## 2. Interview write-up (how to solve it)
Group items by category, then within each group sort by `-rating, content_id`, then slice.

```python
from collections import defaultdict

def top_k_by_category(items, k=3):
    """
    items: iterable of (content_id, category, rating)
    Returns dict {category: [(content_id, rating), ...]} with up to k entries.
    """
    buckets = defaultdict(list)
    for content_id, category, rating in items:
        buckets[category].append((content_id, rating))

    result = {}
    for cat, rows in buckets.items():
        rows.sort(key=lambda r: (-r[1], r[0]))  # highest rating first, then lowest id
        result[cat] = rows[:k]
    return result
```

## 3. Best optimized solution
Use `heapq.nlargest` for O(n log k) per category instead of O(n log n) for a full sort.

```python
import heapq
from collections import defaultdict

def top_k_by_category(items, k=3):
    buckets = defaultdict(list)
    for content_id, category, rating in items:
        # Push as (neg_rating, content_id, content_id, rating) so the heap
        # returns the highest rating and breaks ties by lowest content_id.
        buckets[category].append((-rating, content_id, content_id, rating))

    return {
        cat: [(cid, rating) for _, _, cid, rating in heapq.nlargest(k, rows)]
        for cat, rows in buckets.items()
    }


# --- quick tests ---
def test_top_k():
    items = [
        (1, "A", 4.5), (2, "A", 4.5), (3, "A", 3.0),
        (4, "B", 5.0), (5, "B", 4.7), (6, "B", 4.7), (7, "B", 4.0),
    ]
    out = top_k_by_category(items, k=3)
    assert out["A"] == [(1, 4.5), (2, 4.5), (3, 3.0)]
    assert out["B"] == [(4, 5.0), (5, 4.7), (6, 4.7)]
    assert top_k_by_category([], 3) == {}
    print("ok")
```

### Why it's optimal
- `heapq.nlargest` is O(n log k) vs. O(n log n) for `sort` — meaningful when k is small.
- Single pass to bucket, single pass to heapify each bucket.
- Tie-breaking is explicit and deterministic.

### Common mistakes & interviewer tips
- Returning references to mutable lists — return new lists.
- Not handling ties: two items with rating 4.5 should be ordered stably.
- Tip: ask whether ties are broken by `content_id` ascending or by insertion order. Always state your choice.
