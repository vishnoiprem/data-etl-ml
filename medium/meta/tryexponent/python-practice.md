# Python Practice — Meta DE Technical Screen

Five sample questions from the Exponent guide with worked solutions, edge cases, and trade-off notes.

---

## Q1 — Second letter of the first word

**Prompt:** Given a list of strings, find the second letter of the first word in each string and return the character along with its count of occurrences.

**Clarify first:**
- "Second letter" = index 1 of the first word, assuming 0-indexed.
- What about strings with empty first words or fewer than 2 chars?
- Return type — list of tuples, dict of char → count, or both?

**Solution (clean, readable):**

```python
from collections import Counter

def second_letter_counts(strings):
    second_letters = []
    for s in strings:
        words = s.split()
        if not words or len(words[0]) < 2:
            continue
        second_letters.append(words[0][1])
    return dict(Counter(second_letters))
```

**Edge cases:** empty string → split returns `[]` → skipped. Single-char first word → skipped. Multiple spaces → `split()` handles it (no empty strings).

**Complexity:** O(n · L) where L is average word length. Memory O(k) for k distinct chars.

---

## Q2 — Read CSV with file-not-found handling

**Prompt:** Write a function that reads a `data.csv` file, processes it, and handles a file-not-found exception by outputting "file not found."

**Clarify first:**
- What does "process" mean — count rows, parse columns, return a list of dicts?
- Should we also handle other I/O errors (permission, decode)?

**Solution:**

```python
import csv

def process_csv(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader]
            # Example processing: sum a numeric column called "value"
            total = sum(float(r["value"]) for r in rows if "value" in r)
            return total
    except FileNotFoundError:
        print("file not found")
        return None
```

**Edge cases:** wrong path → prints "file not found". Missing column → uses `.get` style guard. Encoding errors → re-raise or log; per the prompt we only catch `FileNotFoundError`.

**Complexity:** O(n) rows, O(n) memory. For large files, stream and aggregate instead of materializing the list.

---

## Q3 — Second-highest salary per department

**Prompt:** Given a dictionary of employees with their department and salary, find the second-highest salary in each department.

**Clarify first:**
- Input shape — `{emp_id: {"dept": ..., "salary": ...}}` or a list of dicts?
- What if a department has only one employee? Return None, omit, or raise?

**Solution:**

```python
from collections import defaultdict

def second_highest_per_dept(employees):
    by_dept = defaultdict(list)
    for emp in employees:
        by_dept[emp["dept"]].append(emp["salary"])

    result = {}
    for dept, salaries in by_dept.items():
        unique_sorted = sorted(set(salaries), reverse=True)
        result[dept] = unique_sorted[1] if len(unique_sorted) >= 2 else None
    return result
```

**Edge cases:** single-employee dept → `None`. All same salary → `None` after `set()`. Empty input → empty dict.

**Complexity:** O(n log n) due to sort per dept; O(n) memory. Heap-based (`nlargest(2, ...)`) is O(n) per dept if it matters.

---

## Q4 — Join two lists and sort

**Prompt:** Join two lists and sort the result.

**Solution:**

```python
def join_and_sort(a, b):
    return sorted(a + b)
```

If they want dedup first: `sorted(set(a + b))`.

**Complexity:** O((n+m) log(n+m)). For very large lists, `sorted(a + b)` is fine; `heapq.merge` gives a streaming O(n+m) merge if both inputs are already sorted — worth mentioning.

**Edge cases:** mixed types → `TypeError`. None values → TypeError on `<`. Clarify expected element type.

---

## Q5 — Remove items by key

**Prompt:** Remove items from a list based on a specific key.

**Clarify first:**
- "A specific key" — what key? Likely a dict field or a function predicate.
- "Remove" — return a new list, or mutate in place?
- Match by value, predicate, or condition?

**Solution (predicate-based, immutable):**

```python
def remove_by_key(items, key, value):
    """Remove items where items[key] == value."""
    return [item for item in items if item.get(key) != value]
```

**Predicate-based variant:**

```python
def remove_where(items, predicate):
    return [item for item in items if not predicate(item)]
```

**In-place variant (preserves order):**

```python
def remove_in_place(items, key, value):
    items[:] = [item for item in items if item.get(key) != value]
```

**Edge cases:** key missing → `dict.get` returns `None`, so removed if `value != None`. List of non-dicts → `AttributeError`; guard with `isinstance` if needed.

**Complexity:** O(n) time, O(n) memory for the list-comp version; in-place keeps memory flat.

---

## Meta-tips for the Python half

- **Readability > cleverness.** Meta interviewers prefer clear code; no one-liners that need decoding.
- **Function signature first.** Type the `def` line before the body; it forces you to clarify inputs/outputs.
- **Walk through edge cases out loud:** empty list, single element, duplicates, missing keys.
- **Ask about syntax.** "Should I use `csv.DictReader` or `pandas`?" is a fair clarifying question — pick what's appropriate for the data scale.
- **Don't gold-plate.** A correct, simple solution beats an over-engineered one that hits the test cases.