# SWE Coding Sub-Lesson 3 — Strings (reverse, anagram check, substring search)

> **Strings are the third most common SWE coding pattern.** 15-20% of LeetCode medium problems are string problems. The FDE signal: a candidate who knows the difference between `str.split()` and `str.partition()`, can implement KMP for substring search, and handles Unicode correctly — is showing they can debug string-handling code in production. **This sub-lesson covers 3 sub-patterns: reverse, anagram check, substring search.**

---

## Why strings are the FDE signal

The 3 things the interviewer is testing:

1. **Can you recognize the pattern?** The 3 sub-patterns (reverse, anagram check, substring search) cover 80% of string problems.
2. **Can you handle Unicode?** Strings can be ASCII, UTF-8, or Unicode. The candidate who uses `len(s)` vs `len(s.encode('utf-8'))` correctly is showing depth.
3. **Can you write clean string code?** Python's string methods are powerful. The candidate who uses `s[::-1]` for reverse, `s.split()` for tokenize, `s.startswith()` for prefix check — is showing they know the standard library.

**The FDE pattern:** clarify → brute force → optimize → code → test. Same as arrays and hash tables, but the data type is `str`.

---

## Sub-pattern 1: Reverse

**The pattern:** reverse a string in-place (for arrays) or create a new string. O(n) time, O(n) space.

**When to use:** reverse words in a sentence, reverse a substring, check palindrome.

**The template:**

```python
def reverse_string(s: str) -> str:
    return s[::-1]

def reverse_words(s: str) -> str:
    return " ".join(s.split()[::-1])
```

**Sample problem 1: Valid Palindrome**

> Given a string, check if it is a palindrome (considering only alphanumeric characters, ignoring case).

```python
def is_palindrome(s: str) -> bool:
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]
```

**Time:** O(n). **Space:** O(n).

**Sample problem 2: Reverse Words in a String**

> Given a string, reverse the order of words.

```python
def reverse_words(s: str) -> str:
    return " ".join(reversed(s.split()))
```

**Time:** O(n). **Space:** O(n).

**The 3 edge cases:** empty string, single word, multiple spaces between words.

---

## Sub-pattern 2: Anagram Check

**The pattern:** use a frequency counter (hash table) to check if two strings have the same character counts. O(n) time, O(1) space (26 letters) or O(n) space (Unicode).

**When to use:** anagram check, group anagrams, find anagrams in a string.

**The template:**

```python
from collections import Counter

def is_anagram(s: str, t: str) -> bool:
    return Counter(s) == Counter(t)
```

**Sample problem 1: Valid Anagram (covered in 02-hash-tables.md)**

**Sample problem 2: Find All Anagrams in a String**

> Given two strings `s` and `p`, return the start indices of `p`'s anagrams in `s`.

```python
def find_anagrams(s: str, p: str) -> list[int]:
    if len(p) > len(s):
        return []
    p_count = Counter(p)
    window_count = Counter(s[:len(p)])
    result = [0] if window_count == p_count else []
    for i in range(len(p), len(s)):
        window_count[s[i]] += 1
        window_count[s[i - len(p)]] -= 1
        if window_count[s[i - len(p)]] == 0:
            del window_count[s[i - len(p)]]
        if window_count == p_count:
            result.append(i - len(p) + 1)
    return result
```

**Time:** O(n). **Space:** O(1) (26 letters) or O(k) where k is the alphabet size.

**The 3 edge cases:** empty `p`, `p` longer than `s`, no anagrams found.

---

## Sub-pattern 3: Substring Search

**The pattern:** find a substring in a string. O(n + m) time using KMP or Rabin-Karp, O(n × m) time using naive.

**When to use:** find first occurrence, find all occurrences, count occurrences.

**The template (naive):**

```python
def find_substring_naive(s: str, pattern: str) -> int:
    """Return the index of the first occurrence of pattern in s, or -1."""
    for i in range(len(s) - len(pattern) + 1):
        if s[i:i + len(pattern)] == pattern:
            return i
    return -1
```

**The template (KMP):**

```python
def kmp_failure(pattern: str) -> list[int]:
    """Compute the failure function for KMP."""
    failure = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k > 0 and pattern[k] != pattern[i]:
            k = failure[k - 1]
        if pattern[k] == pattern[i]:
            k += 1
        failure[i] = k
    return failure

def kmp_search(s: str, pattern: str) -> int:
    """Return the index of the first occurrence of pattern in s, or -1."""
    failure = kmp_failure(pattern)
    k = 0
    for i in range(len(s)):
        while k > 0 and pattern[k] != s[i]:
            k = failure[k - 1]
        if pattern[k] == s[i]:
            k += 1
        if k == len(pattern):
            return i - len(pattern) + 1
    return -1
```

**Sample problem 1: Implement strStr()**

> Return the index of the first occurrence of `needle` in `haystack`, or -1.

```python
def str_str(haystack: str, needle: str) -> int:
    if not needle:
        return 0
    return kmp_search(haystack, needle)
```

**Time:** O(n + m). **Space:** O(m).

**Sample problem 2: Longest Substring Without Repeating Characters (covered in 01-arrays.md)**

**The 3 edge cases:** empty needle, needle longer than haystack, no occurrence.

---

## Python string gotchas

The 4 things that trip up candidates:

1. **`s.split()` vs `s.split(' ')`:** `s.split()` splits on any whitespace and removes empty strings; `s.split(' ')` splits on single space and keeps empty strings.
2. **`s[::-1]` vs `reversed(s)`:** `s[::-1]` returns a new string; `reversed(s)` returns an iterator.
3. **`s.startswith()` vs `s[:len(prefix)] == prefix`:** `s.startswith()` is more readable and handles edge cases.
4. **`len(s)` vs `len(s.encode('utf-8'))`:** `len(s)` returns the number of Unicode characters; `len(s.encode('utf-8'))` returns the number of bytes.

**The FDE answer:** "Python strings are Unicode by default. `len(s)` returns the number of characters, not bytes. For byte-level operations, use `s.encode('utf-8')`."

---

## The 5 anti-patterns for strings

1. **Jumping to code without a plan.** "I'll just start coding" is a junior answer. The plan is the signal.
2. **Skipping the edge cases.** Empty string, single character, all same characters. The edge cases are the signal.
3. **Not handling Unicode.** ASCII-only assumptions break on real data. The candidate who mentions Unicode is showing depth.
4. **Using the wrong string method.** `s.find()` vs `s.index()` (find returns -1, index raises). The data structure choice is the signal.
5. **Not naming the complexity.** "O(n) time, O(n) space" is the FDE answer. "It's fast" is a junior answer.

---

## The 5 SWE coding etiquette rules for strings

1. **Clarify the problem first.** "Is the string ASCII or Unicode? Are spaces significant? Should I handle case?" The questions are the signal.
2. **State the brute force.** "The naive solution is O(n × m). Can I do better with KMP?" The brute force is the floor.
3. **State the optimized solution.** "I can use KMP for O(n + m)." The optimization is the signal.
4. **Walk through the code out loud.** "I iterate through the string. For each character, I check if it matches the pattern..." The walkthrough is the signal.
5. **Test with edge cases.** "If the string is empty, I return ''. If the pattern is not found, I return -1." The edge cases are the signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the time + space complexity?" | "O(n + m) time, O(m) space. KMP is linear in the input size." |
| 2. "How would you test this?" | "3 cases: empty string, single character, Unicode characters. The edge cases are the canary." |
| 3. "How would you scale this to 1B characters?" | "External sort + map-reduce. Or a streaming algorithm with O(1) memory. The trade-off is accuracy vs memory." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../practical-coding/README.md` | The AI-assisted coding round (the new norm) |
| `../swe-coding/01-arrays.md` | The 2 pointers / sliding window / prefix sum patterns |
| `../swe-coding/02-hash-tables.md` | The frequency counter / two-sum / group by patterns |

---

## The thesis

**Strings are the third most common SWE coding pattern.** The candidate who knows the difference between `str.split()` and `str.partition()`, can implement KMP for substring search, and handles Unicode correctly — is showing they can debug string-handling code in production.

**The 3 sub-patterns (reverse, anagram check, substring search) cover 80% of string problems.** The 2 sample problems per sub-pattern (6 total) are the muscle memory. Practice them out loud, time yourself at 25 minutes per problem, and rehearse with an AI assistant.

**General prep gets you past the resume screen. SWE coding prep gets you past the classic LeetCode round at Anthropic, OpenAI, Palantir, and AWS FDE.**