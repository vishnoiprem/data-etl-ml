# Stickers to Spell Word - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/stickers-to-spell-word

## The Problem
```
Given an array of stickers (strings of lowercase letters) and a target string,
each sticker can be used multiple times. Each use applies ALL the characters
of the sticker (subtracts them from what's needed).

Return the minimum number of stickers needed to spell the target.
If impossible, return -1.

Examples:
    stickers=["with","example","science"], target="thehat" -> 3
    stickers=["notice","possible"], target="basicbasic" -> -1

Constraints:
- 1 <= stickers.length <= 50
- 1 <= stickers[i].length <= 10
- 1 <= target.length <= 15
```

## How I Think (The Mental Process)

### Step 1: Understand the Game
```
Each sticker use "consumes" letters from what's needed.
The remaining letters form the state.
We want to reach the empty state in minimum steps.
```

### Step 2: The Trick
> "KEY INSIGHT: Search over STATES where each state is the multiset of
> remaining letters needed.
>
> From a state, applying a sticker reduces it by the characters the sticker
> provides. Each application costs 1.
>
> Use BFS or DFS with memoization. The state space is manageable because
> target has at most 15 chars."

### Step 3: State Representation
```
State = Counter of remaining letters needed.
Canonical key for memo = sorted tuple of (char, count) pairs.
E.g., {'a': 1, 'b': 2} -> (('a', 1), ('b', 2))
```

### Step 4: Algorithm
> "1. Pre-process: for each sticker, build Counter of chars (remove chars
>    not in target - they don't help).
> 2. BFS/DFS from initial state (Counter of target).
> 3. For each state, try each sticker:
>    - Apply sticker: subtract overlapping chars.
>    - If state unchanged, skip (sticker provides no useful chars).
>    - Recurse with reduced state.
> 4. Memoize: cache results for each state.
> 5. Return steps when state becomes empty. Return -1 if no solution."

### Step 5: Edge cases
> "- Impossible: any char in target not in any sticker -> -1.
> - Empty target: 0 stickers.
> - Single char: 1 if any sticker has it, else -1.
> - All same letter: depends on total count and sticker count of that letter."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the minimum number of stickers to spell the target string, where each sticker use provides all its characters."

**Key Insight:**
> "State = remaining letters needed. Use BFS or DFS with memoization. From each state, try each sticker, which reduces the state."

**Algorithm:**
> "1. Pre-process stickers (remove chars not in target).
> 2. BFS/DFS from initial state (Counter of target).
> 3. At each state, try each sticker, recursing on the reduced state.
> 4. Memoize: cache minimum stickers needed for each state.
> 5. Return when state is empty, else -1."

**Why this works:**
> "State space is bounded (at most 15 chars in target, each with count <= 15). Memoization ensures we compute each state once."

**Edge cases:**
- Impossible: any char in target not in any sticker -> -1.
- Pre-filter: remove chars not in target from stickers.

**Complexity:**
- Time:  O(S * N) where S = state space, N = number of stickers.
- Space: O(S) for memo.

---

## The 20 Implementations (Simple to Complex)

### Way 1: DFS + memo with state as sorted tuple (BEST - Memorize!)
```python
def stickers_to_spell_word_1(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))
```

### Way 2: Verbose
### Way 3: BFS (state as Counter)
### Way 4: Memoized recursion (state as tuple of (char, count))
### Way 5: Iterative BFS with sorted tuple state
### Way 6: Class-based
### Way 7: DP over character counts (26-dim)
### Way 8: lru_cache decorator
### Way 9: Sorted stickers (most useful first)
### Way 10: Helper functions
### Way 11: Functional reduce style
### Way 12: Iterative BFS with state as tuple
### Way 13: DFS with iterative deepening
### Way 14: Beam search (heuristic-based)
### Way 15: Multiset as tuple of chars
### Way 16: Sorted character string state
### Way 17: Dominated sticker removal
### Way 18: BFS Counter smart
### Way 19: Pre-filter useful stickers
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+----------------+
| Scenario           | Best     | Why            |
+--------------------+----------+----------------+
| Standard           | Way 1    | DFS + memo     |
| Top-down (clean)   | Way 8    | lru_cache      |
| Iterative          | Way 3    | BFS            |
| Small target       | Way 7    | 26-dim vec     |
| Pythonic           | Way 20   | Cleanest       |
+--------------------+----------+----------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| DFS + memo (Way 1) | O(S * N) | O(S) | Best |
| BFS (Way 3) | O(S * N) | O(S) | Same |
| lru_cache (Way 8) | O(S * N) | O(S) | Cleanest |

Where S = number of possible states (bounded by char counts in target).

---

## Walkthrough Example

```
stickers = ["with", "example", "science"]
target = "thehat" = {t:2, h:2, e:1, a:1}

Pre-process:
  with:    {t:1, h:1}
  example: {e:2, a:1}  (x,m,p,l not in target - removed)
  science: {e:2}      (s,c,i,n not in target - removed)

Start: state = {t:2, h:2, e:1, a:1}

Try 'with': new state = {t:1, h:1, e:1, a:1}  (reduced)
  Try 'with': {t:0, h:0, e:1, a:1} = {e:1, a:1}  (reduced)
    Try 'example': {e:0, a:0} = empty! return 0
    Total: 1 + 1 + 1 = 3

Try 'with': {t:1, h:1, e:1, a:1}
  Try 'example': {t:1, h:1} (e:1-2=0 removed, a:1-1=0 removed)
    Try 'with': {} return 0
    Total: 1 + 1 + 1 = 3

Minimum = 3.
```

---

## Best Answer to Memorize

```python
def minStickers(stickers, target):
    from collections import Counter
    target_chars = set(target)
    sticker_counts = []
    for sticker in stickers:
        cnt = Counter(sticker)
        for c in list(cnt.keys()):
            if c not in target_chars:
                del cnt[c]
        if cnt:
            sticker_counts.append(cnt)

    memo = {}

    def helper(state):
        if not state:
            return 0
        key = tuple(sorted(state.items()))
        if key in memo:
            return memo[key]

        best = float('inf')
        for sc in sticker_counts:
            new_state = state.copy()
            reduced = False
            for c, cnt in sc.items():
                if c in new_state:
                    new_state[c] -= cnt
                    reduced = True
                    if new_state[c] <= 0:
                        del new_state[c]
            if not reduced:
                continue
            sub = helper(new_state)
            if sub != -1:
                best = min(best, 1 + sub)

        memo[key] = -1 if best == float('inf') else best
        return memo[key]

    return helper(Counter(target))
```

**~20 lines. O(S * N) time. O(S) space. Interview-ready!**

---

## Key Insights

### Why Counter for state?
> "We need a multiset (chars with counts). Counter is the natural Python
> representation. Sorted tuple gives a hashable memo key."

### Why pre-process stickers?
> "Sticker chars not in target are useless. Remove them to reduce work."

### Why check "reduced" flag?
> "Sticker may not provide ANY char needed (or only chars already satisfied).
> Skip such stickers to avoid infinite loops."

### Why memoize?
> "Same state can be reached via different paths. Memoization ensures we
> compute minimum steps once."

### Why DFS vs BFS?
> "Both work. DFS with memo is typically faster. BFS guarantees shortest
> path naturally but uses more memory."

### What's the state space size?
> "At most 15 chars in target, each with count 1-15. State space is bounded
> by product of counts, manageable."

---

## Test Cases

| stickers | target | Expected | Notes |
|----------|--------|----------|-------|
| ["with","example","science"] | "thehat" | 3 | Standard |
| ["notice","possible"] | "basicbasic" | -1 | Impossible |
| ["a"] | "a" | 1 | Single match |
| ["a"] | "b" | -1 | No match |
| ["ab","cd"] | "abcd" | 2 | Two stickers |
| ["abc"] | "abcabc" | 2 | Reuse needed |
| ["these","guess","about","garden","him"] | "atomher" | 3 | LeetCode |
| ["old","station","sign"] | "stupid" | -1 | Missing u, p |
| ["w","o","r","d"] | "word" | 4 | Each char separate |

---

## Common Pitfalls

1. **Wrong "no reduction" check**: Use a flag, not len comparison (some chars may reduce without being removed).
2. **Forgetting to pre-process**: Stickers with no useful chars waste work.
3. **Hash collision in memo key**: Include chars AND counts in key.
4. **Not memoizing**: Exponential blowup without memo.
5. **Wrong base case**: Empty state returns 0, not 1.

---

## Why This Problem Matters

> "Tests:
> 1. State space search with memoization.
> 2. Multiset representation.
> 3. Optimization: pre-filter, prune useless moves.
> 4. Foundation for: BFS/DFS on state spaces, subset covering."

---

## Beyond This Problem: Related Patterns

### 1. Word Ladder (LC 127)
```python
# BFS on words (each word = state).
```

### 2. Shortest Path in Grid
```python
# BFS on grid positions.
```

### 3. BFS on Multisets
```python
# General: state = multiset of items, transition = remove items.
```

### 4. Minimum Number of Refueling Stops (LC 871)
```python
# State = position + fuel left.
```

---

## Connection to State Space Search

This problem is a classic state space search:

```
PATTERN:
- State: remaining work needed.
- Transitions: operations that reduce state.
- Goal: reach empty state.
- Optimize: minimum operations.

EXAMPLES:
- Stickers to Spell Word: multiset state.
- Word Ladder: string state.
- Sliding Puzzle: board state.
- Minimum Knight Moves: position state.
```

The key is choosing the right state representation for memoization.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the state representation?
- [ ] Is the state space bounded?
- [ ] Pre-process to remove useless operations.
- [ ] Use Counter or sorted tuple as memo key.
- [ ] Track "reduced" flag, not just length.
- [ ] Return 0 for empty state (base case).
- [ ] Memoize to avoid recomputation.
- [ ] Handle impossible case (-1).

---

## Mathematical Formulation

Let T = target chars (with multiplicities), S = sticker chars.

```
State: multiset of remaining chars.
Transition: apply sticker s -> state' = state - (state ∩ s).
Cost: 1 per transition.

Goal: reach state = {} in minimum cost.

Answer = min cost to reach empty state, or -1 if unreachable.
```

The state space is bounded by the number of multisets of target chars.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 691 - Stickers to Spell Word](https://leetcode.com/problems/stickers-to-spell-word/)
