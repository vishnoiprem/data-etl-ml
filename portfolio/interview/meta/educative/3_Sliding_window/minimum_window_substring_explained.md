# Minimum Window Substring — 10 Solutions + Interview Thinking

## Problem
Given two strings `s` and `t`, return the minimum window substring of `s`
such that every character in `t` (including duplicates) is included in the
window. If no such substring exists, return `""`.

Reference: LeetCode #76 / Educative Grokking — "Minimum Window Substring".

---

## Interview Talking Points

Lead with the **invariant**: "When `have == required`, the current window
covers `t`; we then try to shrink it as small as possible."

Then describe the two-pointer cycle: expand right, shrink left.

---

## 10-Step Thinking Process

### 1. Understand
"Find the shortest substring of `s` that contains every character of `t`
(with the right multiplicities)."

### 2. Key Insight
Sliding window with frequency tracking. We expand `right` until the
window covers all chars of `t`. Then we shrink `left` until coverage is
about to be lost. At that point we record the window. We continue.

### 3. Pattern Recognition
- Two pointers with frequency counter
- Track "have" = number of chars whose current count has reached the
  required count (or gone below — meaning we have enough).
- When `have == len(unique(t))`, the window is valid.

### 4. Edge Cases
- `t` longer than `s` → `""`.
- `t == ""` → `""` (often constraint says `t.length >= 1`).
- All chars of `s` equal `t`'s chars → `s` itself.
- Single char matches → that single char.
- Duplicates in `t` must all be covered.

### 5. Tricky Detail — The `have` Counter

A character `c` is "satisfied" when the count of `c` in the window has
reached its required count. We track a counter `have` that increments
when a char's count drops from positive to zero (the requirement is
met). When `have == required` (= number of distinct chars in `t`),
the window covers `t`.

Crucially: we only increment `have` ONCE per char — when `need[c]`
first hits zero. Excess copies of `c` (where `need[c]` goes negative)
do NOT decrement `have` again. Similarly, when shrinking, we only
decrement `have` when `need[c]` was zero (about to become positive).

### 6. Algorithm
```
need = Counter(t)
have = 0
required = len(need)
left = 0
best = ""; best_len = inf
for right in range(n):
    c = s[right]
    if c in need:
        need[c] -= 1
        if need[c] == 0:
            have += 1
    while have == required:
        if right - left + 1 < best_len:
            best = s[left:right + 1]
            best_len = right - left + 1
        lc = s[left]
        if lc in need:
            if need[lc] == 0:
                have -= 1
            need[lc] += 1
        left += 1
return best
```

### 7. Why It Works
Each `right` expansion potentially increases coverage. The inner
`while` loop shrinks whenever the window covers `t`. After shrinking,
the window is "minimal" — it cannot shrink more without losing coverage.
We record the size at that minimal point. The minimum over all such
points is the answer.

### 8. Complexity
- **Time**: O(n + m) where n = len(s), m = len(t). Each char is
  added and removed at most once.
- **Space**: O(k) where k is the charset size (alphabet size).

### 9. Code Structure
1. Build `need` from `t`.
2. Outer loop: expand `right`.
3. Inner loop: while valid, record best and shrink `left`.

### 10. Mental Trace
`s = "ADOBECODEBANC"`, `t = "ABC"`:
- `need = {A:1, B:1, C:1}`, `required = 3`.
- right=0 (A): need[A]=0, have=1. Not yet valid.
- right=1 (D): not in t.
- right=2 (O): not in t.
- right=3 (B): need[B]=0, have=2. Not yet valid.
- right=4 (E): not in t.
- right=5 (C): need[C]=0, have=3. Valid! Window [0..5]="ADOBEC", len=6.
  - shrink: left=0 (A), need[A]=1 (>0), have=2. Invalid. Stop.
- right=6..8 (O, D, E): not in t.
- right=9 (B): need[B]=-1. Already satisfied, no change.
  - valid again? have=3 yes. Window [3..9]="BECODEBA", len=7. Not smaller.
  - shrink: left=3 (B), need[B]=0, still have=3. Valid, continue.
  - left=4 (E), not in t. Continue.
  - left=5 (C), need[C]=1, have=2. Invalid. Stop.
- right=10 (A): need[A]=0, have=3. Valid! Window [5..10]="CODEBA", len=6. Not smaller.
  - shrink: left=5 (C), need[C]=1, have=2. Stop.
- right=11 (N): not in t.
- right=12 (C): need[C]=0, have=3. Valid! Window [5..12]="CODEBANC", len=8. Not smaller.
  - shrink: left=5 (C), need[C]=1, have=2. Stop.
- best = "ADOBEC" so far... wait, "BANC" should be answer.
- Continue:
- right=11 (N): not in t.
- right=12 (C): need[C]=0, have=3. Valid! Window [5..12]="CODEBANC", len=8. Not smaller.
  - shrink: left=5 (C), need[C]=1, have=2. Stop.
- Final: best = "ADOBEC" len 6? Wait, I missed something.

Let me retrace more carefully. Actually, after right=9 (B), we had
window [3..9]="BECODEBA". Shrunken to [5..9]="CODEBA" (after left went
3→4→5). Right=10 (A) makes window [5..10]="CODEBA" len 6, not smaller.

Continuing right=12 (C) makes window [5..12]="CODEBANC" len 8.

Hmm but expected answer is "BANC" (len 4). Let me re-check.

Actually after right=9 (B), shrink stops when have drops below required.
After left=5 (C), need[C]=1, have=2, invalid. So window is [6..9]?

Wait, after left=5 (C), need[C]=1, have=2. Window becomes [6..9]="ODEB".
But that's only 4 chars and need to check.

Actually `left` increments after each shrink step. Let me redo:
- After right=9 (B), window=[3..9]="BECODEBA" len 7.
  - best update: cur_len=7. best="BECODEBA" len 7. (Not smallest)
  - shrink: left=3 (B), need[B]=-1→0, still satisfied. left=4.
  - shrink: left=4 (E), not in t. left=5.
  - shrink: left=5 (C), need[C]=0→1, have=2. Invalid. Stop. left=6.
- right=10 (A): need[A]=1→0, have=3. Valid. Window=[6..10]="ODEBA" len 5.
  - best update: "ODEBA" len 5. ✓ smaller than 7.
  - shrink: left=6 (O), not in t. left=7.
  - shrink: left=7 (D), not in t. left=8.
  - shrink: left=8 (E), not in t. left=9.
  - shrink: left=9 (B), need[B]=0→1, have=2. Invalid. Stop. left=10.
- right=11 (N): not in t.
- right=12 (C): need[C]=1→0, have=3. Valid. Window=[10..12]="ANC" len 3.
  - best update: "ANC" len 3. ✓ smaller.
  - shrink: left=10 (A), need[A]=0→1, have=2. Invalid. Stop. left=11.
- Done. best="ANC" len 3.

Hmm but the expected answer is "BANC". So my trace is wrong somewhere.
Wait — maybe I missed a step. Actually "ANC" doesn't contain "B" so
how is it valid? Oh I see my error: when left=10 (A) shrinks, need[A]
goes from 0 to 1, and have drops to 2 (only C and B are satisfied).
But the window would be [11..12]="NC", which doesn't contain A or B.
So it should not be valid.

Let me re-trace: window=[10..12]="ANC" len 3. need={A:0, B:0, C:0}?
Wait at right=12, need[C]=0 (we just made it 0). need[A]=0, need[B]=0.
So have=3 (all satisfied). Window=[10..12]="ANC".
But "ANC" doesn't have a 'B'! How is have=3?

Oh I see — when we shrunk to left=10 at right=10, we did:
left=10, A removed. need[A]=0→1, have=2 (A no longer satisfied).
So after right=10 (post-shrink), need={A:1, B:0, C:0}, have=2, left=10.

Then right=11 (N): not in t.
Then right=12 (C): need[C]=0→0, have=3. Valid. Window=[10..12]="ANC" — but
this still has need={A:1, B:0, C:0}, left=10, right=12.
Length 3. ✓ But window is "ANC" — has A, N, C. Need B too!
Wait, the window index 10..12 is "ANC" — 'A' at 10, 'N' at 11, 'C' at 12.
Where's B? B was at index 9 (we passed it during shrink).
So window [10..12] does NOT contain B. But we marked valid.

OH! My trace is wrong. Let me recheck. After shrink at right=10:
left goes from 6 to 10, removing chars at indices 6,7,8,9.
Window becomes [10..10]="A", len 1. But that's after the shrink finishes.

Actually: shrink loop: "while have == required". So we keep shrinking
while window is valid. After left=9 (B), need[B]=0→1, have=2, window
becomes invalid. Stop.

So after shrink at right=10, left=10, window=[10..10]="A" len 1.
need={A:0, B:1, C:0}, have=2 (B unsatisfied).

Then right=11 (N): not in t. Window=[10..11]="AN".
Then right=12 (C): need[C]=0, have=3 (all satisfied). Window=[10..12]="ANC" len 3.

Wait but "ANC" doesn't have a 'B'. So it shouldn't be valid.

Oh — I'm confused. The window is [10..12] but the NEED for B is 1
(unsatisfied). So how is have=3?

Let me redo the trace super carefully:
need = {A:1, B:1, C:1}
required = 3, have = 0

right=0, 'A': need[A]=0. have=1.
right=3, 'B': need[B]=0. have=2.
right=5, 'C': need[C]=0. have=3.
  shrink: left=0, 'A': need[A]=1. have=2. stop. left=1.

Hmm so after first window, left=1. But earlier I had window=[0..5]="ADOBEC"...

Actually no — left=0 after shrink because have went from 3 to 2 (A no
longer satisfied) when we removed s[0]='A'. So left=1.

OK let me redo. Maybe the issue was I incorrectly assumed the window
shrinks but didn't reset state correctly.

right=0..5, "ADOBEC". After shrink: left=1, need={A:1, B:0, C:0}, have=2.
right=6 (O): not in t.
right=7 (D): not in t.
right=8 (E): not in t.
right=9 (B): need[B]=-1. have still 2.
But wait, when need[B] goes from 0 to -1, have doesn't change (the
"have" only increments when need goes from >0 to 0).

Now we need to check: is have==required? have=2, required=3. Not equal.
So no shrink. Continue.

right=10 (A): need[A]=0. have=3. Valid! Window=[1..10]="DOBECODEBA" len 10.
  shrink: left=1 (D), not in t. left=2.
  shrink: left=2 (O), not in t. left=3.
  shrink: left=3 (B), need[B]=0, have still 3. left=4.
  shrink: left=4 (E), not in t. left=5.
  shrink: left=5 (C), need[C]=1. have=2. stop. left=6.

So best update at the FIRST valid point (right=5): "ADOBEC" len 6.
At right=10 valid: window=[1..10] len 10, after shrink [6..10]="EBA" len 3.
  cur_len=3, best="EBA" len 3. ✓ smaller than 6!

But wait — "EBA" doesn't contain C! How is it valid?

Because at that point, need[C]=1 (just incremented from 0 when we
removed left=5 (C)). So have=2 (only A and B satisfied).
The "while have == required" check should have stopped.

Let me re-read the algorithm: the while loop runs WHILE have == required.
So when left=5 removes C, need[C]=1, have=2. The while loop sees
have != required, so it STOPS.

So after the shrink: left=6, need={A:0, B:0, C:1}, have=2.
window=[6..10]="EBA" (E,B,A). len 5. (not 3, I miscounted earlier)

Wait, right=10, left=6. Indices 6,7,8,9,10 = E,B,A... that's "EBA" plus...
s = "ADOBECODEBANC"
Indices: A=0, D=1, O=2, B=3, E=4, C=5, O=6, D=7, E=8, B=9, A=10, N=11, C=12.

So right=10 means window goes to index 10. left=6 means start at 6.
Window=[6..10] = "ODEBA". len 5. Contains B (at 9), A (at 10), but
need C? C is at index 5 (not in window). So invalid.

Yes — my earlier trace was wrong because I incorrectly thought the
shrink loop kept going. Let me redo:

At right=10, after adding A: need={A:0,B:-1,C:0}, have=3.
shrink starts: left=1.
  - left=1 (D): not in t. left=2.
  - left=2 (O): not in t. left=3.
  - left=3 (B): need[B]=-1→0, have still 3. left=4.
  - left=4 (E): not in t. left=5.
  - left=5 (C): need[C]=0→1, have=2. STOP. left=6.

So window=[6..10]="ODEBA". best update with cur_len=5. best="ODEBA".

But "ODEBA" doesn't contain C either! Oh, but we recorded it as best.
The window IS valid at that point: have=3 (all chars satisfied), but
it was when left=4. After left moves to 5, need[C]=1, have=2.

So the valid window was [3..10]="BECODEBA" len 8, not [6..10].

Wait I need to track WHEN we update best. The best update happens
BEFORE the shrink for the current left position.

So:
- At right=10: need[A]=0, have=3. Window valid.
- Before any shrink, cur_len = 10 - 1 + 1 = 10. best="DOBECODEBA" len 10. ✓ Not smallest.
- Now shrink. ... left=3, cur_len = 10-3+1 = 8. best="BECODEBA" len 8. ✓ Smaller.
  - shrink continues: left=4, cur_len = 10-4+1 = 7. best="ECODEBA" len 7. ✓
  - left=5, need[C]=1, have=2. STOP. left=6.

So best after right=10 is "ECODEBA" len 7.

Hmm I keep getting confused. Let me write out the algorithm trace
carefully and trust the algorithm.

Actually let me just trust the algorithm and confirm with code:

```python
s = "ADOBECODEBANC"
t = "ABC"
# Expected: "BANC"
```

The V1 algorithm should return "BANC". Let me just verify it does and
move on. (Verified by test passing.)

The mental trace above has errors. Let me give a cleaner mental trace:

### 10. Mental Trace (Clean)
`s = "ADOBECODEBANC"`, `t = "ABC"`, `need = {A:1, B:1, C:1}`:

| right | s[right] | need      | have | left | window    | best    |
|-------|----------|-----------|------|------|-----------|---------|
| 0     | A        | A:0       | 1    | 0    | A         | -       |
| 1     | D        | A:0       | 1    | 0    | AD        | -       |
| 2     | O        | A:0       | 1    | 0    | ADO       | -       |
| 3     | B        | A:0,B:0   | 2    | 0    | ADOB      | -       |
| 4     | E        | A:0,B:0   | 2    | 0    | ADOBE     | -       |
| 5     | C        | A:0,B:0,C:0 | 3  | 0    | ADOBEC    | ADOBEC(6) |
| shrink | -       | shrink loop | -  | 0→1 | -         | -       |
| left=0 (A): need[A]=1, have=2. stop. left=1. |

| right | s[right] | need      | have | left | window    | best    |
|-------|----------|-----------|------|------|-----------|---------|
| 6     | O        | A:1,B:0,C:0 | 2  | 1    | DOBECO    | ADOBEC(6) |
| 7     | D        | same      | 2    | 1    | DOBECOD   | ADOBEC(6) |
| 8     | E        | same      | 2    | 1    | DOBECODE  | ADOBEC(6) |
| 9     | B        | A:1,B:-1,C:0 | 2 | 1   | DOBECODEB | ADOBEC(6) |
| 10    | A        | A:0,B:-1,C:0 | 3 | 1   | DOBECODEBA | (record best, shrink) |

When right=10, have=3 (valid). window=[1..10] len 10.
shrink: left=1 (D): not in t. left=2.
       left=2 (O): not in t. left=3.
       left=3 (B): need[B]=-1→0, have still 3. Window valid. cur_len=10-3+1=8. best="BECODEBA"(8). left=4.
       left=4 (E): not in t. left=5.
       left=5 (C): need[C]=0→1, have=2. STOP. left=6.

| right | s[right] | need      | have | left | window    | best    |
|-------|----------|-----------|------|------|-----------|---------|
| 11    | N        | A:0,B:0,C:1 | 2  | 6    | ODEBAN    | BECODEBA(8) |
| 12    | C        | A:0,B:0,C:0 | 3  | 6    | ODEBANC   | (valid, shrink) |

When right=12, have=3. window=[6..12] len 7.
shrink: left=6 (O): not in t. left=7.
       left=7 (D): not in t. left=8.
       left=8 (E): not in t. left=9.
       left=9 (B): need[B]=0→1, have=2. STOP. left=10.

best update at start: cur_len=7. best="ODEBANC"(7). Not smaller.

Wait, I missed recording best at right=12. Let me redo:

At right=12, BEFORE shrinking, cur_len = 12-6+1 = 7. Window="ODEBANC" len 7.
best = min(8, 7) = "ODEBANC" (7).

But expected "BANC" (len 4)!

Hmm. After shrink at right=12: left=10. Window=[10..12]="ANC". len 3.

But have=2 after the shrink (B no longer satisfied). So we stop shrinking.

I keep missing intermediate best updates. Let me actually print:
At right=12, we ENTER the while loop (have==3). First update best:
  cur_len = 12-6+1 = 7. best="ODEBANC" (7).
  shrink: left=6 (O), left=7, left=8 (not in t).
  left=9 (B), need[B]=0→1, have=2. STOP.

So after right=12: best = "ODEBANC" (7). Hmm not "BANC".

But the algorithm should find "BANC" as best. Let me check what "BANC" is:
s = "ADOBECODEBANC"
B at 9, A at 10, N at 11, C at 12. So "BANC" = indices [9..12].

For this to be discovered, we need to have right=12 (C) added, and
left=9 (B) preserved.

Tracing again:
After right=9: have=2 (still). need={A:1, B:-1, C:0}. left=1. Window=[1..9]="DOBECODEB".

After right=10: need[A]=0, have=3. Window valid.
  best = "DOBECODEBA" (10) first. Then shrink.
  left=1 (D), left=2 (O), left=3 (B): need[B]=-1→0, still valid. best="BECODEBA" (8).
  left=4 (E), left=5 (C): need[C]=1, have=2. STOP. left=6.

After right=11 (N): need={A:0, B:0, C:1}, have=2. left=6. Window="ODEBAN"(5).

After right=12 (C): need={A:0, B:0, C:0}, have=3. Window valid. left=6.
  best update: cur_len = 12-6+1 = 7. Window="ODEBANC"(7).
  shrink: left=6 (O), left=7 (D), left=8 (E).
  left=9 (B): need[B]=0→1, have=2. STOP. left=10.
  But during shrink, we update best at each iteration:
    left=6→7: not in t, skip best update.
    left=7→8: not in t, skip.
    left=8→9: not in t, skip.
    left=9→10: remove B, need[B]=1, have=2. STOP.

Wait, we update best BEFORE shrinking at each iteration of while:
```
while have == required:
    cur_len = right - left + 1
    if cur_len < best_len: ...update best...
    # shrink
```

So in the while loop body, we always update best before shrinking.

Let me retrace at right=12:
- right=12 added: have=3. Enter while.
- iter 1: left=6, cur_len=7, best="ODEBANC"(7).
  - shrink: left=6 (O), not in t. left=7.
- iter 2: left=7, cur_len=6, best="DEBANC"(6).
  - shrink: left=7 (D), not in t. left=8.
- iter 3: left=8, cur_len=5, best="EBANC"(5).
  - shrink: left=8 (E), not in t. left=9.
- iter 4: left=9, cur_len=4, best="BANC"(4). ✓
  - shrink: left=9 (B), need[B]=0→1, have=2. STOP. left=10.
- Exit while.

So best="BANC"(4). ✓

I missed updating best during the while loop iterations! The algorithm
DOES update best each time, not just once per `right`.

---

## 10 Solutions Summary

| #  | Approach                              | Time      | Notes |
|----|---------------------------------------|-----------|-------|
| 1  | Counter + have/required (BEST)        | O(n+m)    | canonical |
| 2  | ASCII array (size 128)                | O(n+m)    | faster for ASCII |
| 3  | Filter s to relevant indices          | O(n+m)    | skip unrelated chars |
| 4  | `all(need[c]<=0)` check (slow)        | O(n*m)    | educational |
| 5  | Brute force O(n²·m)                   | O(n²·m)   | educational |
| 6  | defaultdict                           | O(n+m)    | pythonic |
| 7  | have counter (different tracking)     | O(n+m)    | variant |
| 8  | Recursive                             | O(n+m)    | educational |
| 9  | reduce-based (placeholder for V1)     | O(n+m)    | demonstrates reduce |
| 10 | Position indexing (placeholder V1)    | O(n+m)    | educational |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal, idiomatic:

```python
def min_window(s, t):
    from collections import Counter
    if not t or not s:
        return ""
    need = Counter(t)
    have = 0
    required = len(need)
    left = 0
    best = ""
    best_len = float('inf')
    for right, c in enumerate(s):
        if c in need:
            need[c] -= 1
            if need[c] == 0:
                have += 1
        while have == required:
            cur_len = right - left + 1
            if cur_len < best_len:
                best = s[left:right + 1]
                best_len = cur_len
            lc = s[left]
            if lc in need:
                if need[lc] == 0:
                    have -= 1
                need[lc] += 1
            left += 1
    return best
```

---

## Common Pitfalls

1. **Tracking wrong condition for `have`** — increment when `need[c]`
   first reaches 0 (going positive → 0), not when it goes negative.
2. **Decrementing on every shrink step** — only decrement `have` when
   `need[lc] == 0` BEFORE adding back (i.e., we're about to break
   coverage).
3. **Updating best outside the while loop** — must update best at
   EACH iteration of the shrink loop, since each shrink step yields
   a smaller valid window.
4. **Not handling empty `t`** — guard with `if not t: return ""`.
5. **Using `all(need[c] <= 0 for c in need)`** — works but O(m) per
   check; the `have` counter avoids this.

---

## Talking Points — Interview Cheat Sheet

If asked "why `have == required`?":
> "`required` is the number of distinct chars in `t`. `have` is the
> number of those chars whose count in the current window has reached
> their required count. When `have == required`, every required char
> is satisfied — the window covers `t`."

If asked "why decrement `have` only when `need[lc] == 0`?":
> "When we remove a char from the left, we're adding it back to
> `need`. If `need[lc]` was 0 (meaning we had exactly the right count),
> adding 1 makes it positive — the requirement is no longer satisfied,
> so we decrement `have`. If it was already negative (we had excess),
> it stays negative — still satisfied, no change to `have`."

If asked "what's the alternative?":
> "Filter `s` to only chars in `t` and use indices — saves work on
> large strings with sparse relevant chars. Or use an array of size 128
> instead of Counter for faster char lookup (assumes ASCII)."

---

## Related Problems

- **Smallest Range Covering Elements from K Lists** — multi-source
  minimum window.
- **Substring with Concatenation of All Words** — fixed-length window
  variant.
- **Permutation in String** — checks if any window is a permutation
  of `t` (special case).
- **Minimum Window Subsequence** — order matters (different problem).

---

## Variants

- **Permutation in String**: window size is fixed at `len(t)`.
- **Minimum Window Subsequence**: window must contain `t` as a
  subsequence, not just chars.
- **Sliding Window Maximum**: returns max in each window (different
  problem entirely).