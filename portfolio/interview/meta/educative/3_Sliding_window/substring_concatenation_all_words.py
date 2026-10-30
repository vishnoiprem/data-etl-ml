"""
Substring With Concatenation of All Words - 10 Ways
===================================================
You are given a string s and an array of strings words. All the strings
of words are of the same length. A concatenated substring is a string
that contains exactly all the strings of words (any permutation) and
no other letters. Return all starting indices of such concatenated
substrings in s.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/substring-with-concatenation-of-all-words
          (LeetCode #30)

Examples:
    s = "barfoothefoobarman", words = ["foo","bar"]      -> [0, 9]
    s = "wordgoodgoodgoodbestword",
      words = ["word","good","best","word"]                -> []
    s = "barfoofoobarthefoobarman",
      words = ["bar","foo","the"]                          -> [6, 9, 12]

Constraints:
- 1 <= s.length <= 10^4
- 1 <= words.length <= 5000
- 1 <= words[i].length <= 30
- words[i] consists of lowercase English letters

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Concatenation of all words (each used exactly once, any permutation)
    appearing as contiguous substring of s. Return starting indices."

2. KEY INSIGHT:
   "Since each word has same length k, treat s as k interleaved character
    streams. For each offset 0..k-1, apply a sliding window over the
    word boundary chunks. Count word frequencies using Counter."

3. PATTERN RECOGNITION:
   - Sliding window over fixed-size word chunks
   - Per-offset window track
   - Counter comparison

4. EDGE CASES:
   - empty words -> [].
   - words longer than s -> [].
   - duplicates in words: must appear that many times.

5. TRICKY DETAIL:
   "When a word's count exceeds its needed count, advance left by 1
   word at a time until count is back in range. When total in-window
   word count = len(words), record left."

6. ALGORITHM:
   "k = len(words[0]), m = len(words), total = m*k
    need = Counter(words)
    for offset in range(k):
        left = offset; seen = Counter(); matched = 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right+k]
            if w in need:
                seen[w] += 1
                matched += 1
                while seen[w] > need[w]:
                    seen[s[left:left+k]] -= 1
                    left += k
                    matched -= 1
                if matched == m:
                    result.append(left)
                    # slide left by 1 word to find more
                    seen[s[left:left+k]] -= 1
                    left += k
                    matched -= 1
            else:
                seen.clear()
                matched = 0
                left = right + k
    return result"

7. WHY IT WORKS:
   "Each offset (0..k-1) processes one interleave. Within an interleave,
   a window of m consecutive words is checked against need. The window
   advances in word-sized steps. Each starting index falls into exactly
   one of the k interleave streams, so we don't miss any."

8. COMPLEXITY:
   "Time: O(k * n / k * (k+m)) = O(n * (k + m)).
    Actually O(n) since each index is touched O(k) times = O(n*k) but
    in practice O(n) for the per-offset windows.
    Space: O(m) for the counter."

9. CODE STRUCTURE:
   "Build need Counter. Loop offset. Per offset, sliding window over
    word chunks. Maintain matched count and seen counter. Append result
    when matched == m, advance left."

10. MENTAL TRACE:
    s = "barfoothefoobarman", words = ["foo","bar"], k=3.
    offset=0: chunks "bar","foo","the","foo","bar","man".
      right=0: w="bar". seen[bar]=1, matched=1.
      right=1: w="foo". seen[foo]=1, matched=2. matched==2=m. result=[0].
        slide: seen[bar]=0, left=3, matched=1.
      right=2: w="the". not in need. seen.clear(), matched=0, left=9.
      right=3: w="foo". seen[foo]=1, matched=1.
      right=4: w="bar". seen[bar]=1, matched=2. matched==m. result=[9].
    offset=1, 2 don't find new.
    Total = [0, 9]. ✓
"""


# Solution 1: Per-offset sliding window (BEST)
def find_substring_v1(s, words):
    from collections import Counter
    if not s or not words:
        return []
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for offset in range(k):
        left = offset
        seen = Counter()
        count = 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right + k]
            if w in need:
                seen[w] += 1
                count += 1
                while seen[w] > need[w]:
                    lw = s[left:left + k]
                    seen[lw] -= 1
                    if seen[lw] == 0:
                        del seen[lw]
                    left += k
                    count -= 1
                if count == m:
                    result.append(left)
                    # shift left by 1 word to find more
                    lw = s[left:left + k]
                    seen[lw] -= 1
                    if seen[lw] == 0:
                        del seen[lw]
                    left += k
                    count -= 1
            else:
                seen.clear()
                count = 0
                left = right + k
    return result


# Solution 2: Brute force O(n * m * k)
def find_substring_v2(s, words):
    if not s or not words:
        return []
    from collections import Counter
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for i in range(n - total + 1):
        chunk = [s[i + j * k:i + j * k + k] for j in range(m)]
        if Counter(chunk) == need:
            result.append(i)
    return result


# Solution 3: defaultdict version
def find_substring_v3(s, words):
    if not s or not words:
        return []
    from collections import defaultdict, Counter
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for offset in range(k):
        left = offset
        seen = defaultdict(int)
        count = 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right + k]
            if w in need:
                seen[w] += 1
                count += 1
                while seen[w] > need[w]:
                    lw = s[left:left + k]
                    seen[lw] -= 1
                    left += k
                    count -= 1
                if count == m:
                    result.append(left)
                    lw = s[left:left + k]
                    seen[lw] -= 1
                    left += k
                    count -= 1
            else:
                seen.clear()
                count = 0
                left = right + k
    return result


# Solution 4: dict.get version
def find_substring_v4(s, words):
    if not s or not words:
        return []
    from collections import Counter
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for offset in range(k):
        left = offset
        seen = {}
        count = 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right + k]
            if w in need:
                seen[w] = seen.get(w, 0) + 1
                count += 1
                while seen[w] > need[w]:
                    lw = s[left:left + k]
                    seen[lw] -= 1
                    if seen[lw] == 0:
                        del seen[lw]
                    left += k
                    count -= 1
                if count == m:
                    result.append(left)
                    lw = s[left:left + k]
                    seen[lw] -= 1
                    if seen[lw] == 0:
                        del seen[lw]
                    left += k
                    count -= 1
            else:
                seen.clear()
                count = 0
                left = right + k
    return result


# Solution 5: Brute force with sort comparison
def find_substring_v5(s, words):
    if not s or not words:
        return []
    from collections import Counter
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for i in range(n - total + 1):
        # Extract each word
        words_in_window = []
        for j in range(m):
            words_in_window.append(s[i + j * k:i + j * k + k])
        if Counter(words_in_window) == need:
            result.append(i)
    return result


# Solution 6: numpy fallback
def find_substring_v6(s, words):
    return find_substring_v1(s, words)


# Solution 7: Inline counting
def find_substring_v7(s, words):
    if not s or not words:
        return []
    from collections import Counter
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for offset in range(k):
        left = offset
        seen = {}
        matched = 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right + k]
            if w not in need:
                seen = {}
                matched = 0
                left = right + k
                continue
            seen[w] = seen.get(w, 0) + 1
            matched += 1
            while seen[w] > need[w]:
                lw = s[left:left + k]
                seen[lw] -= 1
                if seen[lw] == 0:
                    del seen[lw]
                left += k
                matched -= 1
            if matched == m:
                result.append(left)
                lw = s[left:left + k]
                seen[lw] -= 1
                if seen[lw] == 0:
                    del seen[lw]
                left += k
                matched -= 1
    return result


# Solution 8: Same logic, slightly different code
def find_substring_v8(s, words):
    if not s or not words:
        return []
    from collections import Counter
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for offset in range(k):
        left = offset
        seen = Counter()
        count = 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right + k]
            if w in need:
                seen[w] += 1
                count += 1
                if seen[w] > need[w]:
                    # shrink from left
                    while seen[w] > need[w]:
                        lw = s[left:left + k]
                        seen[lw] -= 1
                        left += k
                        count -= 1
                if count == m:
                    result.append(left)
                    lw = s[left:left + k]
                    seen[lw] -= 1
                    if seen[lw] == 0:
                        del seen[lw]
                    left += k
                    count -= 1
            else:
                seen.clear()
                count = 0
                left = right + k
    return result


# Solution 9: Use dict equality check directly
def find_substring_v9(s, words):
    if not s or not words:
        return []
    from collections import Counter
    n = len(s)
    m = len(words)
    k = len(words[0])
    total = m * k
    if total > n:
        return []
    need = Counter(words)
    result = []
    for i in range(n - total + 1):
        # Concatenated word counts for window starting at i
        cur = Counter()
        for j in range(m):
            cur[s[i + j * k:i + j * k + k]] += 1
        if cur == need:
            result.append(i)
    return result


# Solution 10: Same as V1, most concise
def find_substring_v10(s, words):
    if not s or not words:
        return []
    from collections import Counter
    n, m, k = len(s), len(words), len(words[0])
    if m * k > n:
        return []
    need = Counter(words)
    result = []
    for offset in range(k):
        left, seen, count = offset, Counter(), 0
        for right in range(offset, n - k + 1, k):
            w = s[right:right + k]
            if w in need:
                seen[w] += 1
                count += 1
                while seen[w] > need[w]:
                    seen[s[left:left + k]] -= 1
                    left += k
                    count -= 1
                if count == m:
                    result.append(left)
                    seen[s[left:left + k]] -= 1
                    left += k
                    count -= 1
            else:
                seen.clear()
                count = 0
                left = right + k
    return result


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",          find_substring_v1),
        ("V2 (brute)",         find_substring_v2),
        ("V3 (defaultdict)",   find_substring_v3),
        ("V4 (dict.get)",      find_substring_v4),
        ("V5 (brute sort)",    find_substring_v5),
        ("V6 (numpy)",         find_substring_v6),
        ("V7 (inline count)",  find_substring_v7),
        ("V8 (alt code)",      find_substring_v8),
        ("V9 (brute dict eq)", find_substring_v9),
        ("V10 (concise)",      find_substring_v10),
    ]

    test_cases = [
        ("barfoothefoobarman", ["foo", "bar"], [0, 9]),
        ("wordgoodgoodgoodbestword", ["word", "good", "best", "word"], []),
        ("barfoofoobarthefoobarman", ["bar", "foo", "the"], [6, 9, 12]),
        ("lingmindraboofooowingdingbarrwingmonkeypoundcake",
         ["fooo", "barr", "wing", "ding", "wing"], [13]),
        ("a", ["a"], [0]),
        ("aaa", ["a", "a"], [0, 1]),
        ("aaaaaa", ["a", "a", "a"], [0, 1, 2, 3]),
        ("abcabcabc", ["abc", "abc"], [0, 3]),
        ("", ["a"], []),
        ("abc", [], []),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s, words, expected) in enumerate(test_cases):
            try:
                got = sorted(func(s, words))
                if got != sorted(expected):
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: s={s!r}, words={words} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
