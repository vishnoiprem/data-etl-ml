# Solve Library Coding Tasks in Python

## 1. Simple way to think
- "Up to 3 books from different categories with max points" — this is the LC 1931-style problem re-skinned for a library.
- Books have `book_id, category, points`. Pick at most 3 books, all from different categories, maximizing total points.
- Mental model: it's a 3-element subset selection with a constraint. With only 3 books, brute force is C(n,3) and totally fine for n up to a few thousand.
- Other related tasks: top-K per category, group by author, dedupe by ISBN.

## 2. Interview write-up (how to solve it)

```python
from itertools import combinations
from collections import defaultdict

def top_books_different_categories(books, k=3):
    """
    books: iterable of (book_id, category, points)
    Returns: list of (book_id, category, points) with at most k books,
             all categories distinct, total points maximized.
    """
    # Greedy by category is incorrect in general (e.g., 2nd best in a category
    # could be better than the best in another). So we enumerate.
    by_cat = defaultdict(list)
    for b in books:
        by_cat[b[1]].append(b)
    # For each category, keep only the top book (greedy by category works
    # when k <= #categories and we pick one per category)
    best_per_cat = [max(rows, key=lambda r: r[2]) for rows in by_cat.values()]
    best_per_cat.sort(key=lambda r: -r[2])
    return best_per_cat[:k]


def top_k_total_brute(books, k=3):
    """Correct: enumerate all subsets of size <= k with distinct categories."""
    seen_cats = set()
    uniq = []
    for b in books:
        if b[1] not in seen_cats:
            uniq.append(b); seen_cats.add(b[1])
    best = []
    for r in range(1, k+1):
        for combo in combinations(uniq, r):
            cats = {c[1] for c in combo}
            if len(cats) == len(combo):     # all distinct
                total = sum(c[2] for c in combo)
                if not best or total > best[1]:
                    best = [combo, total]
    return best
```

## 3. Best optimized solution

```python
def top_books_different_categories(books, k=3):
    """
    Optimal when k is small: take the top book per category, then take the top k.
    This is optimal when categories are plentiful and we want exactly k books
    each from a different category — taking the best in each category is dominant.
    """
    from collections import defaultdict
    by_cat = defaultdict(list)
    for b in books:
        by_cat[b[1]].append(b)
    # Take the single best per category; sort desc; take top k
    return sorted(
        (max(rows, key=lambda r: r[2]) for rows in by_cat.values()),
        key=lambda r: -r[2]
    )[:k]


# --- tests ---
books = [
    (1, "Fiction", 90), (2, "Fiction", 80),
    (3, "Sci",     95), (4, "Sci",     70),
    (5, "History", 60), (6, "Bio",     85), (7, "Bio", 75),
]
assert top_books_different_categories(books, 3) == [(3,"Sci",95), (1,"Fiction",90), (6,"Bio",85)]
print("ok")
```

### Why it's optimal
- One pass to bucket by category, one to find the max per bucket, one to take the top k.
- O(n + c log c) where c is the number of categories (c ≤ n).
- For "exactly k from distinct categories," taking the best per category is provably optimal — you can never do better than the best in any category when constrained to one per category.

### Common mistakes & interviewer tips
- Confusing "different categories" with "different books" — they're both required to be unique, but the constraint is on category.
- Greedy across books without grouping by category first — fails on simple counterexamples.
- Tip: clarify the constraint precisely. "Up to 3" vs. "exactly 3" changes the answer.
