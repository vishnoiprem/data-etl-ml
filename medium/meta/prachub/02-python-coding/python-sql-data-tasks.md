# Solve Python and SQL Data Tasks (Flatten + Aggregation)

## 1. Simple way to think
- Part 1: `flatten(nested)` should turn `[[1, [2, 3]], 4, [[5]]]` into `[1, 2, 3, 4, 5]`.
- Two natural approaches: recursion (clear) or iterative stack (no recursion-depth issues).
- Part 2: a typical SQL aggregation — e.g., per-category totals, with a HAVING filter and an ORDER BY.
- For Python, edge cases: empty input, deeply nested, mixed scalars & lists, non-int values.

## 2. Interview write-up (how to solve it)

```python
def flatten(nested):
    """
    Recursively flatten an arbitrarily nested list of ints into a single flat list.
    """
    out = []
    for x in nested:
        if isinstance(x, (list, tuple)):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out
```

```sql
-- Example aggregation: top categories by total revenue, only those with > 1000
SELECT category, SUM(revenue) AS total_revenue
FROM sales
WHERE sale_date >= DATE '2025-01-01'
GROUP BY category
HAVING SUM(revenue) > 1000
ORDER BY total_revenue DESC
LIMIT 10;
```

## 3. Best optimized solution

```python
def flatten(nested):
    """
    Iterative O(n) flatten using an explicit stack.
    Avoids Python's recursion limit (default 1000).
    """
    out = []
    stack = list(nested)[::-1]   # reverse so we pop in original order
    while stack:
        item = stack.pop()
        if isinstance(item, (list, tuple)):
            stack.extend(reversed(item))   # preserve order
        else:
            out.append(item)
    return out


# --- tests ---
assert flatten([1, [2, 3], [[4, 5], 6]]) == [1, 2, 3, 4, 5, 6]
assert flatten([]) == []
assert flatten([[[[1]]]]) == [1]
assert flatten(7) == [7]            # scalar passes through
deep = list(range(2000))
nested = deep
for _ in range(10):                # 10 levels deep, 2000 elements
    nested = [nested]
assert flatten(nested) == deep      # iterative version handles this
print("ok")
```

```sql
-- Optimized SQL with covering index
CREATE INDEX idx_sales_date_category_revenue
  ON sales (sale_date, category, revenue);

SELECT category,
       SUM(revenue)                          AS total_revenue,
       COUNT(DISTINCT customer_id)           AS unique_customers
FROM sales
WHERE sale_date >= DATE '2025-01-01'
GROUP BY category
HAVING SUM(revenue) > 1000
ORDER BY total_revenue DESC
LIMIT 10;
```

### Why it's optimal
- Python: iterative stack is O(n) and stack-safe; `reversed` preserves element order.
- SQL: covering index serves WHERE + GROUP BY; HAVING filters post-aggregation efficiently.
- Adding `COUNT(DISTINCT customer_id)` is a free metric since the scan is already happening.

### Common mistakes & interviewer tips
- Recursing without a base case for empty lists (most do, but be explicit).
- Mutating the input — keep it pure.
- Tip: ask whether `tuple`s should be flattened too. In Python, they're often treated like lists.
