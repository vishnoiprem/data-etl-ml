# Remove Duplicate Letters - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/remove-duplicate-letters

## The Problem
```
Given a string s (lowercase letters), remove duplicate letters so that:
1. Each letter appears exactly once in result
2. The result is smallest in lexicographical order

The result must be a SUBSEQUENCE of s using each unique char once.

Examples:
    bcabc        -> abc
    cbacdcbc     -> acdb
    abacabad     -> abcd
    bbcaaccd     -> bacd
    bbab         -> ab  (bba, bbc, ... wait, ab is valid subsequence)

Constraints:
- 1 <= s.length <= 10^4
- s consists of lowercase English letters
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "bcabc"

Unique chars: {a, b, c}
We need a 3-char string using each once, smallest in lex order.
Subsequences using each once: "bcabc" -> can we get "abc"?
Yes: take b@pos=0, a@pos=2, c@pos=4 → "bac"... that's bigger than "abc"
Try: a@pos=2, b@pos=3, c@pos=4 → "abc" ✓
Smaller than "bac", so "abc" is answer.

Trace step by step:
- i=0, b: stack=[], push b. stack=[b]
- i=1, c: stack[-1]=b, b<c? No. push c. stack=[b,c]
- i=2, a: 
  - stack[-1]=c, c>a AND last[c]=4 > 2. pop c. stack=[b]
  - stack[-1]=b, b>a AND last[b]=3 > 2. pop b. stack=[]
  - push a. stack=[a]
- i=3, b: a<b? No. push b. stack=[a,b]
- i=4, c: b<c? No. push c. stack=[a,b,c]

Result: "abc" ✓
```

### Step 2: The Trick
> "For each char c at index i:
>   - If c already in result, skip
>   - Pop chars from stack that are > c (better lex earlier)
>     BUT only if they appear AGAIN later in s (safe to pop)
>   - Push c
>
> Three conditions to pop: stack non-empty, top > c, last[top] > i"

### Step 3: Why Stack?
> "The result is built left-to-right. We may need to REPLACE earlier chars
> if a smaller char comes. Stack lets us pop from the END.
> Pre-computing last occurrence gives confidence the pop is safe."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to remove duplicate letters while keeping result smallest in
> lex order. The result must be a subsequence of s using each unique char once."

**Key Insight:**
> "This is GREEDY + STACK! For each char c:
> - SKIP if already in result
> - POP chars from stack that are bigger than c, IF they appear again later
> - PUSH c
>
> 'Bigger but reappears later' means we can put it later, freeing space for
> the smaller char to come earlier."

**Algorithm:**
> "1. Pre-compute last occurrence index for each char
> 2. Initialize empty stack, visited set
> 3. For each i, char c in s:
>    - If c in visited, continue (skip)
>    - While stack and stack[-1] > c and last[stack[-1]] > i:
>      * Pop stack, remove from visited
>    - Push c, add to visited
> 4. Join stack"

**Why this works:**
> "When c arrives, it 'threatens' any bigger char on stack. If that bigger
> char appears LATER in s, we can pop it now and add it later - making room
> for c earlier (smaller lex)."
>
> "If bigger char has NO later occurrence, we MUST keep it (otherwise
> result would miss it)."

**Edge cases:**
- All same char: just one instance
- Already sorted unique: result as-is
- Reverse sorted: full reverse to sorted
- All distinct: keep original order

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack + last_index (BEST - Memorize!)
```python
def removeDuplicateLetters(s):
    last_index = {}
    for i, c in enumerate(s):
        last_index[c] = i
    stack = []
    visited = set()
    for i, c in enumerate(s):
        if c in visited:
            continue
        while stack and stack[-1] > c and last_index[stack[-1]] > i:
            visited.remove(stack.pop())
        stack.append(c)
        visited.add(c)
    return ''.join(stack)
```

### Way 2: Same as Way 1, verbose
### Way 3: With count array
### Way 4: Permutations (educational, O(n!))
### Way 5: Recursive try-exclude
### Way 6: Iterative of Way 5
### Way 7: Cleaner variables

### Way 8-12: Variations
- Way 8: With Counter
- Way 9: One-liner style
- Way 10: Explicit comparator
- Way 11: Greedy from end
- Way 12: Class-based

### Way 13-16: Specialized
- Way 13: Most elegant
- Way 14: With deque
- Way 15: With re.sub
- Way 16: Pre-compute as list

### Way 17-20: Variations
- Way 17: Greedy min tracking
- Way 18: Track first occurrences
- Way 19: Compact with helper
- Way 20: Final cleanest

---

## Decision Tree

```
+------------------+------------+--------------+
| Scenario         | Best       | Why          |
+------------------+------------+--------------+
| Most efficient   | Stack      | O(n)         |
| Educational      | Recursive  | Simple logic |
| Functional       | Recursive  | No mutation  |
+------------------+------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack | O(n) | O(1) - max 26 chars |
| Recursive | O(n²) | O(n) |
| Permutations | O(n!) | O(n!) |

---

## Walkthrough Example

```
s = "cbacdcbc"
last_index = {c:4, b:6, a:2, d:3}

i=0, c: not in visited. stack=[]. push. stack=[c]. visited={c}
i=1, b: not in visited. stack[-1]=c, c>b AND last[c]=4 > 1. pop c. stack=[]
      push b. stack=[b]. visited={b}
i=2, a: not in visited. stack[-1]=b, b>a AND last[b]=6 > 2. pop b. stack=[]
      push a. stack=[a]. visited={a}
i=3, c: not in visited. stack[-1]=a, a>c? No. push c. stack=[a,c]. visited={a,c}
i=4, d: not in visited. stack[-1]=c, c>d? No. push d. stack=[a,c,d]. visited+{d}
i=5, c: in visited. skip
i=6, b: not in visited. stack[-1]=d, d>b AND last[d]=3 > 6? 3>6 No. Don't pop.
      stack[-1]=c, c>b AND last[c]=4 > 6? 4>6 No. Don't pop.
      push b. stack=[a,c,d,b]. visited+{b}
i=7, c: in visited. skip

Result: "acdb" ✓
```

## Best Answer to Memorize

```python
def removeDuplicateLetters(s):
    last_index = {c: i for i, c in enumerate(s)}
    stack = []
    visited = set()
    for i, c in enumerate(s):
        if c in visited:
            continue
        while stack and stack[-1] > c and last_index[stack[-1]] > i:
            visited.remove(stack.pop())
        stack.append(c)
        visited.add(c)
    return ''.join(stack)
```

**11 lines. O(n) time. Clean. Interview-ready!**

## Key Insights

### Why "last_index[stack[-1]] > i"?
> "If top of stack's last occurrence is > i (current position), it will
> appear AGAIN later. We can safely remove it now - we'll add it back later.
> If its last occurrence is <= i, removing now would lose it from result."

### Why "stack[-1] > c"?
> "We want smallest lex result. If top is bigger and we can drop it,
> putting smaller c earlier is better."

### Why visited set?
> "Each unique letter appears exactly once. visited tracks which have been added."

### Why NOT Counter approach?
> "Counter would count but lose order info. We need ORDERED access
> (which comes first) for subsequence validity."

## Test Cases

| s | Expected | Why |
|---|----------|-----|
| bcabc | abc | Standard |
| cbacdcbc | acdb | Standard LeetCode |
| abacabad | abcd | All unique |
| bbcaaccd | bacd | 'b' first |
| a | a | Single char |
| aa | a | All same |
| ab | ab | Already sorted unique |
| ba | ba | No duplicates, can't reorder |
| cba | cba | All unique, keep order |
| bbbab | ab | 'b' before 'a' valid subsequence? ab = a@3, b@4. Yes |
| ecbacba | eacb | 'e' only once at start |
| leetcode | letcod | All unique chars |

## Common Pitfalls

1. **Using `>=` instead of `>` in pop**: Can lose last occurrence
2. **Forgetting 'in visited' skip**: Duplicate handling
3. **Wrong pop condition**: All 3 conditions needed together
4. **Mutating original string**: Use indices/replacements
5. **Reorder vs subsequence**: Result must be subsequence of s

## Why This Problem Matters

> "Tests:
> 1. Greedy algorithm design (CRITICAL)
> 2. Stack for result building with backtracking
> 3. Pre-computation (last occurrence) for safe pops
> 4. Multiple conditions together (lex + safety)
> 5. Subsequence constraint handling
> 6. Pattern similar to: smallest subsequence, lexicographically smallest"
