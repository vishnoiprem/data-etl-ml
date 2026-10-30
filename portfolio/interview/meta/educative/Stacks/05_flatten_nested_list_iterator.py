"""
Flatten Nested List Iterator
Medium | 30 min

You're given a nested list of integers. Each element is either an integer
or a list whose elements may also be integers or other integer lists.

Implement an iterator to flatten the nested list:
- Constructor: initializes the iterator with the nested list
- hasNext(): returns True if there are still integers left
- next(): returns the next integer

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/flatten-nested-list-iterator

Example:
    nestedList = [[1, 1], 2, [1, 1]]
    Output: [1, 1, 2, 1, 1]

    nestedList = [1, [4, [6]]]
    Output: [1, 4, 6]

Constraints:
- The nested list length is between 1 and 10^4
- Integers are between -10^4 and 10^4
- Each element is either an int or a list
"""


# =============================================================================
# Helper class (would normally be imported)
# =============================================================================
class NestedInteger:
    def __init__(self, value=None, *, _is_int=False):
        if _is_int:
            # This is an integer NestedInteger
            self._value = value
            self._is_integer = True
            self._list = None
        elif isinstance(value, list):
            # This is a list NestedInteger
            self._list = [NestedInteger._from_any(v) for v in value]
            self._is_integer = False
            self._value = None
        else:
            # Auto-detect: int or list
            if isinstance(value, int):
                self._value = value
                self._is_integer = True
                self._list = None
            else:
                raise TypeError(f"Unsupported type: {type(value)}")

    @classmethod
    def _from_any(cls, v):
        if isinstance(v, cls):
            return v
        elif isinstance(v, int):
            return cls(v, _is_int=True)
        elif isinstance(v, list):
            return cls(v)
        else:
            raise TypeError(f"Unsupported: {type(v)}")

    def is_integer(self):
        return self._is_integer

    def get_integer(self):
        return self._value

    def get_list(self):
        return self._list


# =============================================================================
# WAY 1: Stack of iterators (BEST - Memorize!)
# =============================================================================
# THINKING: "Stack of iterators over nested lists. hasNext() advances
#           iterators until top is an integer. next() returns it.
#           Key trick: when has_next finds an integer, it saves the value
#           in self._next_val. next() returns and CLEARS the cached value."
class NestedIterator1:
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


# Cleaner version of Way 1:
class NestedIterator1Clean:
    def __init__(self, nested_list):
        self.stack = [iter(nested_list)]
        self._next_val = None
        self._has_next_flag = False
        # Pre-advance
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
                self._has_next_flag = True
                return
            else:
                self.stack.append(iter(top.get_list()))
        self._has_next_flag = False

    def has_next(self):
        return self._has_next_flag

    def next(self):
        if not self._has_next_flag:
            raise StopIteration
        val = self._next_val
        self._advance()
        return val


# =============================================================================
# WAY 2: Eager flatten (build list upfront)
# =============================================================================
class NestedIterator2:
    def __init__(self, nested_list):
        self.flattened = []
        self._flatten(nested_list)
        self.index = 0

    def _flatten(self, nested_list):
        for item in nested_list:
            if item.is_integer():
                self.flattened.append(item.get_integer())
            else:
                self._flatten(item.get_list())

    def has_next(self):
        return self.index < len(self.flattened)

    def next(self):
        val = self.flattened[self.index]
        self.index += 1
        return val


# =============================================================================
# WAY 3: Stack of NestedIntegers (not iterators)
# =============================================================================
class NestedIterator3:
    def __init__(self, nested_list):
        # Reverse the list so we can pop from the end (stack behavior)
        self.stack = list(reversed(nested_list))

    def has_next(self):
        while self.stack:
            top = self.stack[-1]
            if top.is_integer():
                return True
            self.stack.pop()
            # Push children in reverse order
            children = top.get_list()
            for child in reversed(children):
                self.stack.append(child)
        return False

    def next(self):
        if self.has_next():
            return self.stack.pop().get_integer()
        raise StopIteration


# =============================================================================
# WAY 4: Recursive generator approach
# =============================================================================
class NestedIterator4:
    def __init__(self, nested_list):
        def gen(lst):
            for item in lst:
                if item.is_integer():
                    yield item.get_integer()
                else:
                    yield from gen(item.get_list())
        self.iterator = gen(nested_list)

    def has_next(self):
        # We need to peek - tricky with generator. Use a saved value approach.
        # For simplicity, mark as True until exhausted
        return True  # Will raise StopIteration eventually

    def next(self):
        return next(self.iterator)


# Actually Way 4 needs proper peek handling. Let me make it work:
class NestedIterator4Clean:
    def __init__(self, nested_list):
        def gen(lst):
            for item in lst:
                if item.is_integer():
                    yield item.get_integer()
                else:
                    yield from gen(item.get_list())
        self.gen = gen(nested_list)
        self._next_val = None
        self._has_next = False
        self._advance()

    def _advance(self):
        try:
            self._next_val = next(self.gen)
            self._has_next = True
        except StopIteration:
            self._has_next = False
            self._next_val = None

    def has_next(self):
        return self._has_next

    def next(self):
        if not self._has_next:
            raise StopIteration
        val = self._next_val
        self._advance()
        return val


# =============================================================================
# WAY 5: Stack with explicit index tracking
# =============================================================================
class NestedIterator5:
    def __init__(self, nested_list):
        # Stack of (list, index) pairs
        self.stack = [(nested_list, 0)]
        self._next_val = None
        self._has_next = False
        self._advance()

    def _advance(self):
        while self.stack:
            current_list, idx = self.stack[-1]
            if idx >= len(current_list):
                self.stack.pop()
                continue
            item = current_list[idx]
            # Move index forward
            self.stack[-1] = (current_list, idx + 1)
            if item.is_integer():
                self._next_val = item.get_integer()
                self._has_next = True
                return
            else:
                self.stack.append((item.get_list(), 0))
        self._has_next = False

    def has_next(self):
        return self._has_next

    def next(self):
        if not self._has_next:
            raise StopIteration
        val = self._next_val
        self._advance()
        return val


# =============================================================================
# WAY 6: Using deque
# =============================================================================
from collections import deque

class NestedIterator6:
    def __init__(self, nested_list):
        # Stack of iterators
        self.stack = deque()
        self.stack.append(iter(nested_list))
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

    def has_next(self):
        return self._has_next

    def next(self):
        if not self._has_next:
            raise StopIteration
        val = self._next_val
        self._advance()
        return val


# =============================================================================
# WAY 7: Stack with peek-and-pop
# =============================================================================
class NestedIterator7:
    def __init__(self, nested_list):
        # Pre-process to flatten eagerly
        self.stack = []
        for item in reversed(nested_list):
            self.stack.append(item)
        # Cache for peeked value
        self._cached = None

    def _find_next(self):
        while self.stack:
            top = self.stack[-1]
            if top.is_integer():
                self._cached = top.get_integer()
                self.stack.pop()
                return True
            else:
                self.stack.pop()
                for child in reversed(top.get_list()):
                    self.stack.append(child)
        self._cached = None
        return False

    def has_next(self):
        if self._cached is not None:
            return True
        return self._find_next()

    def next(self):
        if self.has_next():
            val = self._cached
            self._cached = None
            return val
        raise StopIteration


# =============================================================================
# WAY 8: Using yield-based pattern
# =============================================================================
class NestedIterator8:
    def __init__(self, nested_list):
        self.queue = []
        self._dfs(nested_list)

    def _dfs(self, lst):
        for item in lst:
            if item.is_integer():
                self.queue.append(item.get_integer())
            else:
                self._dfs(item.get_list())

    def has_next(self):
        return len(self.queue) > 0

    def next(self):
        return self.queue.pop(0)


# =============================================================================
# WAY 9: With explicit list pre-flattening
# =============================================================================
class NestedIterator9:
    def __init__(self, nested_list):
        self.items = []
        self._preorder(nested_list)
        self.pos = 0

    def _preorder(self, lst):
        for item in lst:
            if item.is_integer():
                self.items.append(item)
            else:
                self._preorder(item.get_list())

    def has_next(self):
        return self.pos < len(self.items)

    def next(self):
        val = self.items[self.pos].get_integer()
        self.pos += 1
        return val


# =============================================================================
# WAY 10: Two-stack approach
# =============================================================================
class NestedIterator10:
    def __init__(self, nested_list):
        self.stack = []  # stack of NestedIntegers
        for item in reversed(nested_list):
            self.stack.append(item)

    def has_next(self):
        while self.stack:
            top = self.stack[-1]
            if top.is_integer():
                return True
            self.stack.pop()
            children = top.get_list()
            for child in reversed(children):
                self.stack.append(child)
        return False

    def next(self):
        if self.has_next():
            return self.stack.pop().get_integer()
        raise StopIteration


# =============================================================================
# WAY 11: Using index-based state machine
# =============================================================================
class NestedIterator11:
    def __init__(self, nested_list):
        # Stack of (list, index) - cleaner state machine
        self.stack = [(nested_list, 0)]
        self._next_val = None
        self._has_next = False
        self._advance()

    def _advance(self):
        while self.stack:
            current, idx = self.stack[-1]
            if idx >= len(current):
                self.stack.pop()
                continue
            item = current[idx]
            self.stack[-1] = (current, idx + 1)
            if item.is_integer():
                self._next_val = item.get_integer()
                self._has_next = True
                return
            else:
                self.stack.append((item.get_list(), 0))
        self._has_next = False
        self._next_val = None

    def has_next(self):
        return self._has_next

    def next(self):
        if not self._has_next:
            raise StopIteration
        val = self._next_val
        self._advance()
        return val


# =============================================================================
# WAY 12: Compact eager
# =============================================================================
class NestedIterator12:
    def __init__(self, nested_list):
        flat = []
        stack = list(reversed(nested_list))
        while stack:
            top = stack.pop()
            if top.is_integer():
                flat.append(top.get_integer())
            else:
                stack.extend(reversed(top.get_list()))
        self.flat = flat
        self.i = 0

    def has_next(self):
        return self.i < len(self.flat)

    def next(self):
        val = self.flat[self.i]
        self.i += 1
        return val


# =============================================================================
# WAY 13: Recursive approach
# =============================================================================
class NestedIterator13:
    def __init__(self, nested_list):
        self.items = []
        self._build(nested_list)
        self.i = 0

    def _build(self, lst):
        for item in lst:
            if item.is_integer():
                self.items.append(item.get_integer())
            else:
                self._build(item.get_list())

    def has_next(self):
        return self.i < len(self.items)

    def next(self):
        val = self.items[self.i]
        self.i += 1
        return val


# =============================================================================
# WAY 14: Using deque for queue (DFS with explicit stack)
# =============================================================================
class NestedIterator14:
    def __init__(self, nested_list):
        # DFS flatten using queue (FIFO doesn't matter for output with this trick)
        # Actually we use stack discipline to maintain order
        stack = []
        for item in reversed(nested_list):
            stack.append(item)
        flat = []
        while stack:
            item = stack.pop()
            if item.is_integer():
                flat.append(item.get_integer())
            else:
                # Push children in reverse so first child is popped first
                children = item.get_list()
                for child in reversed(children):
                    stack.append(child)
        self.flat = flat
        self.i = 0

    def has_next(self):
        return self.i < len(self.flat)

    def next(self):
        val = self.flat[self.i]
        self.i += 1
        return val


# =============================================================================
# WAY 15: Stack of tuples (id, list, index)
# =============================================================================
class NestedIterator15:
    def __init__(self, nested_list):
        self.stack = [(nested_list, 0)]
        self._next_val = None
        self._found = False
        self._advance()

    def _advance(self):
        while self.stack:
            lst, idx = self.stack[-1]
            if idx >= len(lst):
                self.stack.pop()
                continue
            item = lst[idx]
            self.stack[-1] = (lst, idx + 1)
            if item.is_integer():
                self._next_val = item.get_integer()
                self._found = True
                return
            self.stack.append((item.get_list(), 0))
        self._found = False
        self._next_val = None

    def has_next(self):
        return self._found

    def next(self):
        if not self._found:
            raise StopIteration
        val = self._next_val
        self._advance()
        return val


# =============================================================================
# WAY 16: Lazy with explicit stack of NestedIntegers
# =============================================================================
class NestedIterator16:
    def __init__(self, nested_list):
        self.stack = []
        # Reverse for stack order
        for item in reversed(nested_list):
            self.stack.append(item)
        self._next_val = None
        self._has_next = False
        self._prepare()

    def _prepare(self):
        while self.stack:
            top = self.stack[-1]
            if top.is_integer():
                self._next_val = top.get_integer()
                self._has_next = True
                return
            self.stack.pop()
            for child in reversed(top.get_list()):
                self.stack.append(child)
        self._has_next = False

    def has_next(self):
        return self._has_next

    def next(self):
        if not self._has_next:
            raise StopIteration
        val = self._next_val
        # Pop and prepare next
        self.stack.pop()
        self._prepare()
        return val


# =============================================================================
# WAY 17: Iterator-based with saved element
# =============================================================================
class NestedIterator17:
    def __init__(self, nested_list):
        self.stack = [iter(nested_list)]
        self._saved = None
        self._has_saved = False

    def has_next(self):
        if self._has_saved:
            return True
        while self.stack:
            try:
                top = next(self.stack[-1])
            except StopIteration:
                self.stack.pop()
                continue
            if top.is_integer():
                self._saved = top.get_integer()
                self._has_saved = True
                return True
            else:
                self.stack.append(iter(top.get_list()))
        return False

    def next(self):
        if not self.has_next():
            raise StopIteration
        val = self._saved
        self._saved = None
        self._has_saved = False
        return val


# =============================================================================
# WAY 18: Using try-except
# =============================================================================
class NestedIterator18:
    def __init__(self, nested_list):
        self.stack = [iter(nested_list)]

    def has_next(self):
        while self.stack:
            try:
                top = next(self.stack[-1])
            except StopIteration:
                self.stack.pop()
                continue
            if top.is_integer():
                self._val = top.get_integer()
                return True
            else:
                self.stack.append(iter(top.get_list()))
        return False

    def next(self):
        try:
            return self._val
        except AttributeError:
            if self.has_next():
                return self._val
            raise StopIteration


# =============================================================================
# WAY 19: Most compact (eager)
# =============================================================================
class NestedIterator19:
    def __init__(self, nested_list):
        flat = []
        stack = list(reversed(nested_list))
        while stack:
            x = stack.pop()
            if x.is_integer():
                flat.append(x.get_integer())
            else:
                stack.extend(reversed(x.get_list()))
        self.flat = flat
        self.i = -1

    def has_next(self):
        return self.i + 1 < len(self.flat)

    def next(self):
        self.i += 1
        return self.flat[self.i]


# =============================================================================
# WAY 20: Most elegant (clean Way 3 variant)
# =============================================================================
class NestedIterator20:
    def __init__(self, nested_list):
        # Stack of NestedIntegers (not iterators)
        self.stack = list(reversed(nested_list))

    def has_next(self):
        # Unwrap until we find an integer or stack is empty
        while self.stack and not self.stack[-1].is_integer():
            top = self.stack.pop()
            self.stack.extend(reversed(top.get_list()))
        return bool(self.stack)

    def next(self):
        if self.has_next():
            return self.stack.pop().get_integer()
        raise StopIteration


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to design an iterator that flattens a nested list of integers
lazily (without building the entire flat list upfront, ideally)."

Key Insight:
"The challenge with 'next()' and 'hasNext()' is that we need to PEEK
at the next integer without consuming it. The trick is to maintain a
stack of iterators - on hasNext(), unwind the stack until we find an
integer at the top, and 'peek' it. On next(), pop and return it."

Algorithm (Stack of Iterators):
"1. Initialize stack with iter(nestedList)
2. hasNext():
   - While stack:
     * Peek top iterator, advance it
     * If item is integer, save it and return True
     * If item is list, push its iterator onto stack
   - Return False
3. next():
   - hasNext() must have been called first
   - Return the saved value, clear the saved state"

Why stack of iterators:
"EACH iterator lazily traverses ONE level. The stack represents
the current path through nested lists. LIFO matches the DFS traversal:
we go deep into a sublist before coming back."

Why not just flatten upfront:
"For large nested lists, pre-flattening uses O(n) memory upfront.
The iterator approach is O(depth) memory - much better for very
deep, very large structures."

Edge cases:
- Empty nested list: hasNext always False
- All integers, no nesting: works like a normal iterator
- Deeply nested (single chain): stack can grow to depth n
- Recursive list structure: not supported (assume tree-like)

COMPLEXITY:
+----------------+--------+----------+
| Approach       | Time   | Space    |
+----------------+--------+----------+
| Eager flatten  | O(n)   | O(n)     |
| Lazy iterator  | O(n)   | O(d)     |
| Lazy generator | O(n)   | O(d)     |
+----------------+--------+----------+

where n = total elements, d = max nesting depth.

KEY TRICK:
The trick is 'peek' - hasNext() can advance the iterator but
NOT consume the value. Save it as instance state, then next()
returns and clears it.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
def flatten_list(nested_iterator_object):
    """Test helper from problem statement."""
    result = []
    while nested_iterator_object.has_next():
        result.append(nested_iterator_object.next())
    return result


if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack of iterators (BEST)", NestedIterator1Clean),
        ("Way 2: Eager flatten", NestedIterator2),
        ("Way 3: Stack of NestedIntegers", NestedIterator3),
        ("Way 4: Generator-based", NestedIterator4Clean),
        ("Way 5: Stack with index", NestedIterator5),
        ("Way 6: deque", NestedIterator6),
        ("Way 7: Peek-and-pop", NestedIterator7),
        ("Way 8: Queue-based", NestedIterator8),
        ("Way 9: Pre-flattened list", NestedIterator9),
        ("Way 10: Two-stack", NestedIterator10),
        ("Way 11: Index state machine", NestedIterator11),
        ("Way 12: Compact eager", NestedIterator12),
        ("Way 13: Recursive", NestedIterator13),
        ("Way 14: BFS flatten", NestedIterator14),
        ("Way 15: Tuple stack", NestedIterator15),
        ("Way 16: Lazy with NestedIntegers", NestedIterator16),
        ("Way 17: Iterator with saved elem", NestedIterator17),
        ("Way 18: Try-except", NestedIterator18),
        ("Way 19: Most compact", NestedIterator19),
        ("Way 20: Most elegant", NestedIterator20),
    ]

    test_cases = [
        # (nested_list, expected_flat)
        ([[1, 1], 2, [1, 1]], [1, 1, 2, 1, 1]),
        ([1, [4, [6]]], [1, 4, 6]),
        ([], []),
        ([1, 2, 3, 4], [1, 2, 3, 4]),
        ([[]], []),
        ([[[1]]], [1]),
        ([1, [2, [3, [4, [5]]]]], [1, 2, 3, 4, 5]),
    ]

    print("=" * 70)
    print("FLATTEN NESTED LIST ITERATOR - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/flatten-nested-list-iterator")
    print("=" * 70)

    all_pass = True
    for name, cls in implementations:
        all_test_pass = True
        for nested_raw, expected in test_cases:
            try:
                # Convert raw list to NestedInteger (handle ints and lists)
                nested = NestedInteger(nested_raw)
                # The iterator expects a list of NestedIntegers at top level
                # So we wrap as: pass [NestedInteger(...)] to constructor
                # But our implementations expect iter(nestedList)
                # If nested is itself a list NestedInteger, we need its list
                if nested.is_integer():
                    # Single integer wrapped - shouldn't happen in our tests
                    top_list = [nested]
                else:
                    top_list = nested.get_list()
                it = cls(top_list)
                result = flatten_list(it)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: {nested_raw} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on {nested_raw} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
