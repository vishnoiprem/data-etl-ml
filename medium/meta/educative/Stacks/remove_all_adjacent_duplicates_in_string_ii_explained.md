# Remove All Adjacent Duplicates in String II - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/remove-all-adjacent-duplicates-in-string-ii

## The Problem
```
Given a string s and integer k. Repeatedly remove k ADJACENT and
EQUAL characters until no more removals are possible.

Return the final string.

Examples:
    s = "abcd",                k = 2  -> "abcd"          (no removals)
    s = "deeedbbccdde",        k = 3  -> "ddbbccdde"     (removed "eee")
    s = "pbbcggttciiip",       k = 3  -> "pbbcggttcp"    (removed "iii")
    s = "aaa",                 k = 3  -> ""               (all removed)
    s = "aaaa",                k = 3  -> "a"             (1 left)
    s = "aaaabaaaa",           k = 4  -> "b"             (both groups removed)
    s = "abccbc",              k = 2  -> "ac"            (cc removed->b, bb... wait)

Trace "abccbc" with k=2:
    a -> [(a,1)]
    b -> [(a,1),(b,1)]
    c -> [(a,1),(b,1),(c,1)]
    c -> count 2, pop. [(a,1),(b,1)]
    b -> b matches, count 2, pop. [(a,1)]
    c -> different. [(a,1),(c,1)]
    Result: "ac"

Constraints:
- 1 <= s.length <= 10^5
- 2 <= k <= 10^5
- s consists of lowercase English letters
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
The key insight is that removal can CASCADE. When you remove k chars,
the new neighbors might form a new k-group.

Example: "abccbc", k=2
- Initial: a b c c b c
- Remove "cc" -> a b _ _ b c  -> a b b c
- "bb" is now adjacent! -> a _ _ c -> a c
- No more removals. Result: "ac"
```

### Step 2: The Trick
> "Use a STACK of (char, count) tuples!
> - When a char matches the stack top, INCREMENT count.
> - When count reaches k, POP the entry (the k chars are removed).
> - When a char doesn't match the top, push (char, 1).
>
> This handles cascading because when we pop, the NEXT char to arrive
> will compare with the new top of stack (which was previously deeper)."

### Step 3: Why Stack with Counts?
> "We need to know HOW MANY of each char are currently grouped.
> Storing (char, count) lets us:
> - Detect when count reaches k without re-counting
> - Pop efficiently in O(1)
> - Track groups for output (each char repeated by its count)"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to remove k adjacent duplicate characters from a string,
> repeatedly, until no more removals are possible."

**Key Insight:**
> "Use a STACK of (char, count) tuples!
> - For each char:
>   * If it matches stack top, increment count.
>   * If count reaches k, pop the entry.
>   * Otherwise, push (char, 1).
> - At the end, join the stack with each char repeated by its count."

**Algorithm:**
> "1. Initialize empty stack
> 2. For each char c in s:
>    - If stack and stack[-1].char == c:
>      * stack[-1].count += 1
>      * If stack[-1].count == k: pop
>    - Else:
>      * Push (c, 1)
> 3. Return ''.join(c * count for c, count in stack)"

**Why this works (handles cascading):**
> "When we pop because count reached k, the NEXT char's match check
> compares with the NEW top of stack. This new top was previously deeper
> in the stack, so the new char correctly compares with the right
> neighbor (post-cascade)."

**Edge cases:**
- k = 1: First char pushed with count 1, but stack[-1][0] != c only when
  different chars. So k=1 leaves strings unchanged. (k >= 2 in problem.)
- All same chars: count grows until k, pops, then continues.
- Cascading removals: handled naturally by stack depth.

**Complexity:**
- Time: O(n) - each char pushed and popped at most once
- Space: O(n) for the stack

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack of (char, count) - mutable list (BEST - Memorize!)
```python
def removeDuplicates(s, k):
    stack = []  # [char, count]
    for c in s:
        if stack and stack[-1][0] == c:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()
        else:
            stack.append([c, 1])
    return ''.join(c * cnt for c, cnt in stack)
```

### Way 2-3: Variations
- Way 2: Use tuples (rebuild on update)
- Way 3: Parallel stacks (char_stack + count_stack)

### Way 4: Brute force recursive
- Find any k-group, remove, recurse on shorter string.

### Way 5-7: Variations
- Way 5: Counter-based
- Way 6: Mutable list (similar to Way 1)
- Way 7: Modulo check

### Way 9: Recursive approach
- Find first k-group, remove it, recurse.

### Way 10: With Counter dict for char tracking

### Way 11-13: Variations
- Way 11: Index tracking
- Way 12: Modulo
- Way 13: Parallel counts (separate char stack and count stack)

### Way 14: Most elegant - one pass with tuple swap

### Way 15: Generator-based final assembly

### Way 16: Encapsulated with helper functions
```python
def push(c):
    if stack and stack[-1][0] == c:
        stack[-1] = (c, stack[-1][1] + 1)
        return stack[-1][1] == k
    ...
```

### Way 17: List extend in final assembly

### Way 18: Deque-based (no real benefit over list)

### Way 19: Class-based
```python
class StringReducer:
    def __init__(self, k):
        self.k = k
        self.stack = []
    def process(self, c): ...
    def result(self): ...
```

### Way 20: Final cleanest

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Standard         | Way 1    | Clean O(n)   |
| Educational      | Way 4    | Simple       |
| Functional       | Way 4    | Recursive    |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack (Way 1) | O(n) | O(n) |
| Brute recursive | O(n²) | O(n²) |

---

## Walkthrough Example

```
s = "deeedbbccdde", k = 3

Process each char:
- 'd': stack=[(d,1)]
- 'e': stack=[(d,1),(e,1)]
- 'e': stack=[(d,1),(e,2)]
- 'e': count=3 == k=3, POP. stack=[(d,1)]
- 'd': d matches, count=2. stack=[(d,2)]
- 'b': different. stack=[(d,2),(b,1)]
- 'b': count=2. stack=[(d,2),(b,2)]
- 'c': different. stack=[(d,2),(b,2),(c,1)]
- 'c': count=2. stack=[(d,2),(b,2),(c,2)]
- 'd': different. stack=[(d,2),(b,2),(c,2),(d,1)]
- 'd': d matches, count=2. stack=[(d,2),(b,2),(c,2),(d,2)]
  Wait, this would create (d,2) on TOP not merge with the (d,2) at bottom!
- 'e': different. stack=[(d,2),(b,2),(c,2),(d,2),(e,1)]

Result: dd bb cc dd e = "ddbbccdde" ✓
```

Wait, let me re-trace. The stack stores GROUPS, not cumulative counts:

Process each char correctly:
- 'd': new group. stack=[(d,1)]
- 'e': new group. stack=[(d,1),(e,1)]
- 'e': matches e, count=2. stack=[(d,1),(e,2)]
- 'e': count=3==k. POP. stack=[(d,1)]
- 'd': matches d, count=2. stack=[(d,2)]
- 'b': new group. stack=[(d,2),(b,1)]
- 'b': matches b, count=2. stack=[(d,2),(b,2)]
- 'c': new group. stack=[(d,2),(b,2),(c,1)]
- 'c': matches c, count=2. stack=[(d,2),(b,2),(c,2)]
- 'd': new group (different from c). stack=[(d,2),(b,2),(c,2),(d,1)]
- 'd': matches d, count=2. stack=[(d,2),(b,2),(c,2),(d,2)]
- 'e': new group. stack=[(d,2),(b,2),(c,2),(d,2),(e,1)]

Result: d*2 + b*2 + c*2 + d*2 + e*1 = "ddbbccdde" ✓

## Best Answer to Memorize

```python
def removeDuplicates(s, k):
    stack = []  # each element is [char, count]
    for c in s:
        if stack and stack[-1][0] == c:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()
        else:
            stack.append([c, 1])
    return ''.join(c * cnt for c, cnt in stack)
```

**10 lines. O(n) time. Clean. Interview-ready!**

---

## Key Insights

### Why (char, count) tuples?
> "We need to track HOW MANY identical chars are grouped together.
> When count reaches k, we know to pop. This avoids re-scanning."

### How does it handle cascading?
> "When we pop, the next char to arrive compares with the NEW stack top.
> The new top was previously deeper in the stack, so it represents
> the correct neighbor post-cascade removal."

### Why use mutable list [char, count] instead of tuple?
> "Tuples are immutable. With list, we can do `stack[-1][1] += 1`
> in-place. With tuple, we'd rebuild: `stack[-1] = (c, stack[-1][1] + 1)`."

### What about > k duplicates?
> "If k=3 and we have 'aaaaaa' (6 chars):
> - Push a, count 1, 2, 3 -> pop (stack empty)
> - Push a, count 1, 2, 3 -> pop (stack empty)
> Result: ''"

---

## Test Cases

| s | k | Expected | Why |
|---|---|----------|-----|
| abcd | 2 | abcd | No removals |
| deeedbbccdde | 3 | ddbbccdde | eee removed |
| pbbcggttciiip | 3 | pbbcggttcp | iii removed |
| aaa | 3 | "" | All 3 removed |
| aaaa | 3 | a | 1 left after |
| "" | 2 | "" | Empty |
| aa | 2 | "" | 2 removed |
| aabbcc | 2 | "" | All pairs removed |
| ab | 2 | ab | No removals |
| aaaabaaaa | 4 | b | 2 groups of 4 removed |
| abccbc | 2 | ac | Cascading removal |

## Common Pitfalls

1. **Forgetting to update top's count**: When char matches, INCREMENT
   count, don't push a new entry.
2. **Mutating tuples**: Use list [char, count] for in-place updates.
3. **Off-by-one on count**: count starts at 1 when char is pushed.
4. **Wrong check for k**: Use `== k`, not `>= k`. If count overshoots
   it means a previous removal was correct.
5. **Final string construction**: Don't forget to repeat each char
   by its count.

## Why This Problem Matters

> "Tests:
> 1. Stack with grouped counts (CRITICAL)
> 2. Cascading operations handled by stack depth
> 3. Time/space tradeoff (O(n) vs O(n²))
> 4. Pattern similar to: string reduction, k-grouping problems
> 5. Edge case: empty string, all-same string, k > length"
