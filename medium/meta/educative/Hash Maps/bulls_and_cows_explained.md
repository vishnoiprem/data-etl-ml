# Bulls and Cows - 10 Ways with How to Think

## The Problem
```
Bulls: digits in correct position (same value)
Cows: digits in both secret and guess but different positions
Return hint as "xAyB" where x = bulls, y = cows

Example:
    secret = "1807", guess = "7810"
    Bulls: position 1 (8=8) -> 1 bull
    Cows: 1, 0, 7 all in both at different positions -> 3 cows
    Answer: "1A3B"
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
secret = "1807", guess = "7810"

Bulls (same position, same digit):
  Pos 0: 1 vs 7 ✗
  Pos 1: 8 vs 8 ✓ BULL
  Pos 2: 0 vs 1 ✗
  Pos 3: 7 vs 0 ✗
  
Bulls = 1

Cows (same digit, different position):
  7, 1, 0 are in both -> 3 cows
```

### Step 2: The Trick
> "Two passes:
> 1. Count bulls (same position matches)
> 2. For non-bulls, count how many digits appear in BOTH (min of counts)"

### Step 3: Cleaner Approach
> "Use hashmaps to count unmatched digits. Then min(count_secret, count_guess) gives matches."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to count two things: bulls (same position, same digit) and cows (digits in both but different positions)."

**Approach:**
> "I'll use a two-pass approach:
> 1. First pass: count bulls. For non-bulls, track digit frequencies.
> 2. Second pass: for each digit, the number of cows is min(count in secret, count in guess)."

**Why this works:**
> "Bulls are easy - just compare position by position. Cows are trickier. For each digit, the number of times it appears in both secret and guess (excluding bulls) is the cow count. We take min to avoid double counting."

**Edge cases:**
- All bulls: cows = 0
- All cows: bulls = 0
- Duplicates: handled naturally by Counter

---

## The 10 Implementations

### Way 1: Two HashMaps (BEST - Memorize!)
```python
from collections import Counter

def getHint(secret, guess):
    bulls = 0
    secret_count = Counter()
    guess_count = Counter()

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            secret_count[s] += 1
            guess_count[g] += 1

    # Cows = sum of min(counts) for each digit
    cows = sum((secret_count & guess_count).values())

    return f"{bulls}A{cows}B"
```

### Way 2: Single HashMap with Count Diff
```python
def getHint(secret, guess):
    bulls = 0
    cows = 0
    count = {}

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            count[s] = count.get(s, 0) + 1
            count[g] = count.get(g, 0) - 1
            if count[s] <= 0:
                cows += 1
            if count[g] >= 0:
                cows += 1

    return f"{bulls}A{cows // 2}B"
```

### Way 3: Using defaultdict
```python
from collections import defaultdict

def getHint(secret, guess):
    bulls = 0
    secret_count = defaultdict(int)
    guess_count = defaultdict(int)

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            secret_count[s] += 1
            guess_count[g] += 1

    cows = sum(min(secret_count[d], guess_count[d]) for d in secret_count)
    return f"{bulls}A{cows}B"
```

### Way 4: Array-Based Counting (Fastest)
```python
def getHint(secret, guess):
    bulls = 0
    cows = 0
    secret_count = [0] * 10
    guess_count = [0] * 10

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            secret_count[int(s)] += 1
            guess_count[int(g)] += 1

    for i in range(10):
        cows += min(secret_count[i], guess_count[i])

    return f"{bulls}A{cows}B"
```

### Way 5: One-Pass Optimized (O(n))
```python
def getHint(secret, guess):
    bulls = 0
    cows = 0
    count = [0] * 10

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            if count[int(s)] < 0:
                cows += 1
            if count[int(g)] > 0:
                cows += 1
            count[int(s)] += 1
            count[int(g)] -= 1

    return f"{bulls}A{cows}B"
```

### Way 6: Counter Intersection
```python
def getHint(secret, guess):
    bulls = sum(1 for s, g in zip(secret, guess) if s == g)

    s_count = Counter()
    g_count = Counter()
    for s, g in zip(secret, guess):
        if s != g:
            s_count[s] += 1
            g_count[g] += 1

    cows = sum((s_count & g_count).values())
    return f"{bulls}A{cows}B"
```

### Way 7-10: More variations
- Way 7: Helper function
- Way 8: Most compact
- Way 9: List comprehension
- Way 10: Smart tracking

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest code    | Two maps    | Readable     |
| Fastest          | Array       | O(1) lookup  |
| Memory optimal   | One-pass    | No extras    |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Two maps | O(n) | O(1) |
| Array | O(n) | O(1) |
| One-pass | O(n) | O(1) |

---

## Walkthrough Example

```
secret = "1807", guess = "7810"

Pass 1: Count bulls
  Pos 0: 1 vs 7 -> miss
  Pos 1: 8 vs 8 -> BULL! bulls=1
  Pos 2: 0 vs 1 -> miss
  Pos 3: 7 vs 0 -> miss

Non-bull counts:
  secret: {1:1, 0:1, 7:1}
  guess:  {7:1, 1:1, 0:1}

Pass 2: Count cows
  For each digit: min(counts)
  1: min(1,1) = 1
  0: min(1,1) = 1
  7: min(1,1) = 1
  Total cows = 3

Answer: "1A3B" ✓
```

## Best Answer to Memorize

```python
from collections import Counter

def getHint(secret, guess):
    bulls = 0
    secret_count = Counter()
    guess_count = Counter()

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            secret_count[s] += 1
            guess_count[g] += 1

    cows = sum((secret_count & guess_count).values())

    return f"{bulls}A{cows}B"
```

**13 lines. O(n) time. Clean. Interview-ready!** 🚀

## Why min() Works for Cows

```
secret has: 1, 2, 2, 3 (count of '2' is 2)
guess has:  1, 2, 4, 5 (count of '2' is 1)

For digit '2': min(2, 1) = 1 cow
That's correct! Only 1 '2' can match.
```

We use min to avoid double-counting. If secret has two '2's but guess has one '2', we can only form one cow match.

## Test Cases

| secret | guess | Expected | Why |
|--------|-------|----------|-----|
| 1807 | 7810 | 1A3B | 1 bull, 3 cows |
| 1123 | 0111 | 1A1B | 1 bull, 1 cow |
| 1 | 0 | 0A0B | No match |
| 1 | 1 | 1A0B | Perfect match |
| 1234 | 4321 | 0A4B | All cows |
| 1122 | 2211 | 0A4B | All cows |
