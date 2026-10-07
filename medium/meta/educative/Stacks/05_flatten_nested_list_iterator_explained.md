# Flatten Nested List Iterator - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/flatten-nested-list-iterator

## The Problem
```
Given a nested list of integers (each element is either an int or another
list), implement an iterator to flatten it.

Methods to implement:
- __init__(nestedList): Initialize with nested list
- hasNext(): True if more integers
- next(): Return next integer

Examples:
    nestedList = [[1, 1], 2, [1, 1]]
    Output: [1, 1, 2, 1, 1]

    nestedList = [1, [4, [6]]]
    Output: [1, 4, 6]

Constraints:
- List length: 1 to 10^4
- Integers: -10^4 to 10^4
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nestedList = [[1, 1], 2, [1, 1]]

Tree structure:
       []
      / | \
   [1,1] 2  [1,1]
   / \      / \
  1   1    1   1

Flatten (preorder): 1, 1, 2, 1, 1
```

### Step 2: The Trick
> "Use a STACK of ITERATORS!
> - hasNext() advances the iterators at the top
> - When it finds an integer, save it (peek without consuming)
> - When it finds a list, push that list's iterator onto stack
> - When iterator exhausts, pop it and try the next"
> "Why LAZY approach?"
> "Each next() call only does work for ONE integer at a time.
> Memory: O(depth) instead of O(n) for eager flatten."

### Step 3: Why Stack?
> "LIFO matches DFS traversal - we go deep into a sublist before backtracking.
> Each iterator represents one 'level' of the nested structure."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to design an iterator that flattens a nested list. The tricky part is that `hasNext()` and `next()` interact - `hasNext()` can advance the iterator but `next()` consumes."

**Key Insight:**
> "I'll use a stack of iterators. `hasNext()` advances iterators UNTIL the topmost one yields an integer (which it caches but doesn't consume). `next()` returns that cached value and clears the cache."

**Algorithm:**
> "1. Initialize: stack = [iter(nestedList)]
> 2. hasNext():
>    - If cached integer exists, return True
>    - While stack:
>      * Advance top iterator
>      * If integer: cache it, return True
>      * If list: push its iterator onto stack
>      * If exhausted: pop iterator, continue
>    - Return False
> 3. next():
>    - Ensure hasNext() is True (or call it)
>    - Return cached value, clear cache"

**Why this works:**
> "The stack maintains ALL iterators along the current path. When we go deeper, we push. When we exhaust, we pop. LIFO guarantees we return integers in preorder (left-to-right, depth-first)."

**Edge cases:**
- Empty list: hasNext always False
- All integers: works like normal iterator
- Deeply nested: stack grows to depth
- Empty sublists: `[]` - still need to skip them

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack of Iterators (BEST - Memorize!)
```python
class NestedIterator:
    def __init__(self, nested_list):
        self.stack = [iter(nested_list)]
        self._cached = None
        self._has_cached = False

    def has_next(self):
        if self._has_cached:
            return True
        while self.stack:
            try:
                top = next(self.stack[-1])
            except StopIteration:
                self.stack.pop()
                continue
            if top.is_integer():
                self._cached = top.get_integer()
                self._has_cached = True
                return True
            else:
                self.stack.append(iter(top.get_list()))
        return False

    def next(self):
        if not self.has_next():
            raise StopIteration
        val = self._cached
        self._cached = None
        self._has_cached = False
        return val
```

### Way 2: Eager Flatten (Build full list upfront)
```python
class NestedIterator:
    def __init__(self, nested_list):
        self.flat = []
        self._flatten(nested_list)
        self.i = 0

    def _flatten(self, lst):
        for item in lst:
            if item.is_integer():
                self.flat.append(item.get_integer())
            else:
                self._flatten(item.get_list())

    def has_next(self):
        return self.i < len(self.flat)

    def next(self):
        val = self.flat[self.i]
        self.i += 1
        return val
```

### Way 3: Stack of NestedIntegers (Not Iterators)
```python
class NestedIterator:
    def __init__(self, nested_list):
        self.stack = list(reversed(nested_list))

    def has_next(self):
        while self.stack:
            top = self.stack[-1]
            if top.is_integer():
                return True
            self.stack.pop()
            for child in reversed(top.get_list()):
                self.stack.append(child)
        return False

    def next(self):
        if self.has_next():
            return self.stack.pop().get_integer()
        raise StopIteration
```

### Way 4: Generator (Recursive yield-from)
### Way 5: Stack with (list, index) tuples
### Way 6: deque for stack
### Way 7: Peek-and-pop pattern

### Way 8-10: Eager variations
- Way 8: Use list as queue (still DFS due to push order)
- Way 9: Pre-flattened with full info preserved
- Way 10: Two-stack approach

### Way 11-15: Lazy/state-machine variants
- Way 11: State machine with pre-advance
- Way 12: Compact eager with manual stack
- Way 13: Recursive eager
- Way 14: DFS using deque
- Way 15: Tuple stack with pre-advance

### Way 16-20: Specialized
- Way 16: Lazy with NestedIntegers stack
- Way 17: Iterator with saved element
- Way 18: Try-except
- Way 19: Most compact (eager)
- Way 20: Most elegant

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Lazy (large)     | Stack iters | O(depth) mem |
| Eager (simple)   | Pre-flatten | Easy code    |
| Most compact     | Way 19      | Fewest lines |
| Pure functional  | Generator   | yield-from   |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Eager flatten | O(n) | O(n) |
| Lazy iterator | O(n) overall, O(d) per call | O(d) |
| Generator | O(n) overall, O(d) per call | O(d) |

where n = total elements, d = max nesting depth.

---

## Walkthrough Example

```
nestedList = [[1, 1], 2, [1, 1]]

Stack: [iter([[1,1], 2, [1,1]])]

has_next():
  Iter advances: gets [1,1] (a list)
  Not integer, push iter([1,1])
  Stack: [iter(top), iter([1,1])]
  Iter on [1,1] advances: gets 1 (integer)
  Cache = 1
  Return True

next() returns: 1

has_next():
  Iter on [1,1] advances: gets 1 (integer)
  Cache = 1, return True

next() returns: 1

has_next():
  Iter on [1,1] advances: raises StopIteration
  Pop iter([1,1])
  Stack: [iter(top)]
  Iter on top advances: gets 2 (integer)
  Cache = 2, return True

next() returns: 2

... etc.
```

## Best Answer to Memorize

```python
class NestedIterator:
    def __init__(self, nestedList):
        self.stack = [iter(nestedList)]
        self._next_val = None
        self._has_next = False
        self._advance()

    def _advance(self):
        while self.stack:
            try:
                top = next(self.stack[-1])
            except StopIteration:
                self.stack.pop()
                continue
            if top.is_integer():
                self._next_val = top.get_integer()
                self._has_next = True
                return
            else:
                self.stack.append(iter(top.get_list()))
        self._has_next = False

    def hasNext(self):
        return self._has_next

    def next(self):
        if not self._has_next:
            raise StopIteration
        val = self._next_val
        self._advance()
        return val
```

**24 lines. O(d) memory. Lazy. Interview-ready!**

## Key Insights

### The Cache Trick
> "When `has_next()` advances an iterator and finds an integer, it MUST
> cache that integer so it can be returned by `next()` without re-advancing.
> Otherwise `next()` would skip every other integer."

### Why Pre-advance?
> "We call `_advance()` once in `__init__` and again after each `next()`.
> This way `has_next()` is O(1) (just returns a flag) - which is required
> since it's commonly called in a loop."

### Why Stack of Iterators vs List of Items?
> "Iterators give us O(1) access to the NEXT item via `next()`.
> Lists would require us to manage indices ourselves.
> Iterators are slightly cleaner and Pythonic."

## Test Cases

| Input | Expected |
|-------|----------|
| [[1,1], 2, [1,1]] | [1, 1, 2, 1, 1] |
| [1, [4, [6]]] | [1, 4, 6] |
| [] | [] |
| [1, 2, 3, 4] | [1, 2, 3, 4] |
| [[]] | [] |
| [[[1]]] | [1] |
| [1, [2, [3, [4, [5]]]]] | [1, 2, 3, 4, 5] |

## Common Pitfalls

1. **Forgetting to cache**: Skip every other integer
2. **Not handling empty sublists**: Crashes on `[[]]`
3. **Mixing up BFS vs DFS**: BFS gives different order
4. **Not pre-advancing**: First call to `next()` is slow

## Why LeetCode Loves This

> "It's a CLASSIC design problem. Tests:
> 1. Stack understanding
> 2. Iterator protocol design
> 3. Lazy computation
> 4. Edge cases (empty lists, nested empty)
> 5. Cache management between hasNext and next"
