# Isomorphic Strings - 10 Ways with How to Think

## The Problem
```
Check if two strings are isomorphic. A 1-to-1 mapping exists from chars
of one string to chars of the other.

Examples:
    "egg", "add" -> True (e->a, g->d)
    "foo", "bar" -> True (f->b, o->a)
    "badc", "baba" -> False (b AND d both map to 'b')
    "ab", "aa" -> False (a AND b both map to 'a')
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "egg", t = "add"
e -> a, g -> d ✓ (consistent mapping)

s = "foo", t = "bar"
f -> b, o -> a ✓ (consistent, no conflicts)

s = "badc", t = "baba"
b -> b, a -> a, d -> b, c -> a
But b -> b AND d -> b (two chars map to 'b') - INVALID!
```

### Step 2: The Rules
> "For two strings to be isomorphic:
> 1. Each char in s maps to exactly one char in t
> 2. Each char in t is mapped from exactly one char in s
> 3. The mapping preserves order"

### Step 3: Algorithm
> "Two hashmaps:
> - s_to_t: char in s -> char in t
> - t_to_s: char in t -> char in s
> Check both directions to ensure 1-to-1 mapping"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to check if two strings are isomorphic, meaning there's a 1-to-1 mapping between their characters that preserves order."

**Key Insight:**
> "For a valid mapping:
> - Each character in s must map to exactly one character in t
> - Each character in t must be mapped from exactly one character in s
> - This means I need to check BOTH directions"

**Algorithm:**
> "I'll use two hashmaps:
> - s_to_t: char in s -> char in t
> - t_to_s: char in t -> char in s
> For each pair, verify consistency in both directions."

**Why both directions:**
> "If I only check s->t, I might miss the case where two different chars in s map to the same char in t. Example: 'ab' -> 'aa' would pass s->t check but is not isomorphic."

---

## The 10 Implementations

### Way 1: Two HashMaps (BEST - Memorize!)
```python
def isIsomorphic(s, t):
    if len(s) != len(t):
        return False

    s_to_t = {}
    t_to_s = {}

    for c1, c2 in zip(s, t):
        if c1 in s_to_t:
            if s_to_t[c1] != c2:
                return False
        else:
            s_to_t[c1] = c2

        if c2 in t_to_s:
            if t_to_s[c2] != c1:
                return False
        else:
            t_to_s[c2] = c1

    return True
```

### Way 2: Single HashMap + set
```python
def isIsomorphic(s, t):
    if len(s) != len(t):
        return False

    mapping = {}
    seen = set()

    for c1, c2 in zip(s, t):
        if c1 in mapping:
            if mapping[c1] != c2:
                return False
        else:
            if c2 in seen:
                return False
            mapping[c1] = c2
            seen.add(c2)

    return True
```

### Way 3: defaultdict
Uses defaultdict to avoid key checks.

### Way 4: Index pattern (clever!)
```python
def isIsomorphic(s, t):
    return [s.find(c) for c in s] == [t.find(c) for c in t]
```

### Way 5: Using set comparison
```python
def isIsomorphic(s, t):
    return len(set(zip(s, t))) == len(set(s)) == len(set(t))
```

### Way 6: Most compact
```python
def isIsomorphic(s, t):
    return len(s) == len(t) and len(set(s)) == len(set(t)) == len(set(zip(s, t)))
```

### Way 7-10: Variations
- Way 7: Tuple of first indices
- Way 8: Index loop
- Way 9: get default trick
- Way 10: Counter

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest code    | HashMap x2  | Readable     |
| Most compact     | Set         | One line     |
| Elegant          | Index pat   | Clever       |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| HashMaps | O(n) | O(n) |
| Index | O(n²) | O(n) |
| Set | O(n) | O(n) |

---

## Walkthrough Example

```
s = "badc", t = "baba"

Iterate pairs:
  b -> b: s_to_t={b:b}, t_to_s={b:b}
  a -> a: s_to_t={b:b, a:a}, t_to_s={b:b, a:a}
  d -> b: s_to_t has 'd'? No, add d->b
         BUT t_to_s has 'b'? Yes, t_to_s[b] = b, but we want d
         'b' is mapped to 'b' but we want 'd' - CONFLICT!
         Return False ✓
```

## Best Answer to Memorize

```python
def isIsomorphic(s, t):
    if len(s) != len(t):
        return False

    s_to_t = {}
    t_to_s = {}

    for c1, c2 in zip(s, t):
        if c1 in s_to_t:
            if s_to_t[c1] != c2:
                return False
        else:
            s_to_t[c1] = c2

        if c2 in t_to_s:
            if t_to_s[c2] != c1:
                return False
        else:
            t_to_s[c2] = c1

    return True
```

**17 lines. O(n) time. Clean.** 🚀

## Compact Set Version

```python
def isIsomorphic(s, t):
    return len(set(zip(s, t))) == len(set(s)) == len(set(t))
```

## Why Both Directions Matter

```
s = "ab", t = "aa"

Just s->t check:
  a -> a: ok
  b -> a: 'b' not in map, add 'b'->'a'
  ✓ passes s->t check

But this is NOT isomorphic! Why?
  Because 'a' in t is mapped from BOTH 'a' and 'b' in s.
  Need t->s check too:
  a -> a: ok
  b -> a: 'a' is in t_to_s as 'a', but we want 'b'. CONFLICT!
  ✗ fails t->s check
```

## Test Cases

| s | t | Expected | Why |
|---|---|----------|-----|
| egg | add | True | e->a, g->d |
| foo | bar | True | f->b, o->a |
| badc | baba | False | b and d both to 'b' |
| ab | aa | False | a and b both to 'a' |
| "" | "" | True | Empty |
| paper | title | True | p->t, a->i, e->l, r->e |

## Key Insight

> "Two hashmaps ensure 1-to-1 mapping in BOTH directions. A single hashmap would miss cases where multiple chars map to the same char."
