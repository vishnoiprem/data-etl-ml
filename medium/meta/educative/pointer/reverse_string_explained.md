# Reverse String — 0.0001% Expert Guide

> **LeetCode 344** | **Difficulty:** Easy | **Avg Solve Time:** 15 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-string
> **Problem:** `reverseString(s)` — reverse char array in-place with O(1) memory.

---

## 📋 WHAT THE QUESTION ASKS

Given a character array `s`, reverse it **in-place** using O(1) extra memory. Return the (now reversed) array.

### Constraints
- `1 <= s.length <= 1000`
- Each `s[i]` is a printable ASCII character.
- Must be in-place, O(1) extra memory.

### Examples
```
["h","e","l","l","o"]      -> ["o","l","l","e","h"]
["H","a","n","n","a","h"]  -> ["h","a","n","n","a","H"]
["a"]                       -> ["a"]
["a","b"]                   -> ["b","a"]
[]                          -> []
```

### Why This Is "Easy"
- Classic two-pointer pattern.
- O(n) time, O(1) space.
- Foundation for in-place manipulations.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Reverse the array IN-PLACE with O(1) extra space."

### Step 2: Key Insight — Position Pairs
> "Position `i` should swap with position `n-1-i`.
> Pair up: (0, n-1), (1, n-2), ..., swap each pair."

### Step 3: Two Pointers
> "left=0, right=n-1. While left < right:
>   swap s[left], s[right].
>   left++; right--.
> When pointers meet, we're done."

### Step 4: Algorithm
```
1. left=0, right=n-1.
2. While left < right:
     swap s[left], s[right].
     left++; right--.
3. Done.
```

### Step 5: Edge Cases
- Empty: nothing to do.
- Single char: no swap.
- Two chars: one swap.
- Even length: n/2 swaps.
- Odd length: middle char stays.

### Step 6: Code It
```python
def reverseString(s):
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
    return s
```

### Step 7: Verify
["h","e","l","l","o"]: left=0, right=4. Swap → ["o","e","l","l","h"]. left=1, right=3. Swap → ["o","l","l","e","h"]. left=2, right=2. Done. ✓

### Step 8: Trade-offs
- Two-pointer in-place: O(n) time, O(1) space. **BEST**.
- Stack-based: O(n) time, O(n) space. Inefficient.
- New array: O(n) time, O(n) space. Inefficient.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to reverse a char array in-place."

KEY INSIGHT: Two pointers from both ends. Swap inward.
Position i swaps with n-1-i. After n/2 swaps, done.

ALGORITHM:
1. left=0, right=n-1.
2. While left < right:
     swap s[left], s[right].
     left++; right--.

COMPLEXITY: O(n) time, O(1) space.

EDGE CASES:
- Empty/single: nothing to swap.
- Even length: n/2 swaps.
- Odd length: (n-1)/2 swaps, middle stays.

WHY IN-PLACE WORKS:
- Each swap fixes TWO positions.
- After n/2 swaps, all positions are correct.

THE TRICK:
- "Position i ↔ position n-1-i".
- Use Python tuple swap: s[l], s[r] = s[r], s[l].

RELATED:
- Reverse Words in String (LC 151).
- Reverse Vowels (LC 345).
- Reverse Linked List (LC 206).
- Rotate Array (LC 189).
"""
```

---

## 💎 THE 6-LINE SOLUTION (Memorize!)

```python
def reverseString(s):
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
    return s
```

**Time:** `O(n)` | **Space:** `O(1)`

---

## 🤖 KEY INSIGHTS

1. **Two pointers** from both ends.
2. **Swap inward** until pointers meet.
3. **Each swap fixes two positions.**
4. **n/2 swaps** for even length, (n-1)/2 for odd.
5. **Python tuple swap** is clean: `a, b = b, a`.
6. **In-place** = O(1) extra space.
7. **Single pass** = O(n) time.
8. **Middle stays** for odd length.
9. **Empty/single** = no swap needed.
10. **Foundation** for many in-place algorithms.

---

## 🧪 TEST CASES

| Input | Expected | Note |
|-------|----------|------|
| `["h","e","l","l","o"]` | `["o","l","l","e","h"]` | Standard |
| `["H","a","n","n","a","h"]` | `["h","a","n","n","a","H"]` | Even |
| `["a"]` | `["a"]` | Single |
| `["a","b"]` | `["b","a"]` | Two |
| `[]` | `[]` | Empty |
| `["a","b","c"]` | `["c","b","a"]` | Odd |
| `["1","2","3","4"]` | `["4","3","2","1"]` | Even |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Two-pointer in-place** | **O(n)** | **O(1)** | **✅ BEST** |
| Stack | O(n) | O(n) | ❌ Wasteful |
| New array | O(n) | O(n) | ❌ Wasteful |

---

## 🔗 RELATED

- Reverse Words (LC 151)
- Reverse Vowels (LC 345)
- Reverse Linked List (LC 206)
- Rotate Array (LC 189) — uses 3 reversals

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Two pointers from both ends. Swap inward. n/2 swaps total. Python tuple swap = clean."