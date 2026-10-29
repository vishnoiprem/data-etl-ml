"""
Longest Substring Without Repeating Characters - 10 Ways
========================================================
Given a string s, find the length of the longest substring without
repeating characters.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-substring-without-repeating-characters
          (LeetCode #3)

Examples:
    s = "abcabcbb"     -> 3  ("abc")
    s = "bbbbb"        -> 1  ("b")
    s = "pwwkew"       -> 3  ("wke")
    s = ""             -> 0
    s = "abcdef"       -> 6
    s = "abba"         -> 2  ("ab" or "ba")

Constraints:
- 0 <= s.length <= 5 * 10^4
- s consists of English letters, digits, symbols, spaces.

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find the longest substring with all unique characters."

2. KEY INSIGHT:
   "Sliding window with a 'last seen' map. For each char, jump the left
    pointer past the last occurrence of that char. Track max window size."

3. PATTERN RECOGNITION:
   "Two pointers + char->index hashmap. left = max(left, last_index[c]+1)."

4. EDGE CASES:
   - Empty string -> 0.
   - All same char -> 1.
   - All unique -> len(s).
   - Single char -> 1.
   - "abba": left must not retreat — use last_seen[c] only if it's
     within the current window.

5. TRICKY DETAIL:
   "When we see char c at index right, we need left = max(left, last[c]+1).
   Using max prevents left from moving BACKWARD if c was seen BEFORE
   the current window. E.g., 'abba' at right=3 ('a'): last[a]=0, left=0;
   new left = max(0, 0+1) = 1. Correctly doesn't retreat."

6. ALGORITHM:
   "last = {} (default -1)
    left = 0; best = 0
    for right in range(n):
        if s[right] in last and last[s[right]] >= left:
            left = last[s[right]] + 1
        last[s[right]] = right
        best = max(best, right - left + 1)
    return best"

7. WHY IT WORKS:
   "left always points to the start of the current window of unique chars.
   When we encounter a repeat, we jump left past the previous occurrence.
   The 'max(left, last[c]+1)' prevents retreating when the repeat is
   outside the window."

8. COMPLEXITY:
   "Time: O(n) - each char visited once.
    Space: O(min(n, alphabet)) for last_seen map."

9. CODE STRUCTURE:
   "Initialize last seen map (default -1). Iterate: update left, store
    last, update best."

10. MENTAL TRACE:
    s = "abcabcbb":
    right=0 'a': last[a]=-1 (not in window). left=0. last[a]=0. best=1.
    right=1 'b': not in window. left=0. last[b]=1. best=2.
    right=2 'c': not in window. left=0. last[c]=2. best=3.
    right=3 'a': last[a]=0 >= left=0. left=0+1=1. last[a]=3. best=3.
    right=4 'b': last[b]=1 >= left=1. left=1+1=2. last[b]=4. best=3.
    right=5 'c': last[c]=2 >= left=2. left=2+1=3. last[c]=5. best=3.
    right=6 'b': last[b]=4 >= left=3. left=4+1=5. last[b]=6. best=3.
    right=7 'b': last[b]=6 >= left=5. left=6+1=7. last[b]=7. best=3.
    Returns 3. ✓
"""


# Solution 1: Hashmap + max(left, last+1) (BEST)
def longest_unique_v1(s):
    last = {}
    left = 0
    best = 0
    for right, c in enumerate(s):
        if c in last and last[c] >= left:
            left = last[c] + 1
        last[c] = right
        cur = right - left + 1
        if cur > best:
            best = cur
    return best


# Solution 2: ASCII array of size 128
def longest_unique_v2(s):
    last = [-1] * 128
    left = 0
    best = 0
    for right, c in enumerate(s):
        idx = ord(c)
        if last[idx] >= left:
            left = last[idx] + 1
        last[idx] = right
        cur = right - left + 1
        if cur > best:
            best = cur
    return best


# Solution 3: defaultdict for last seen
def longest_unique_v3(s):
    from collections import defaultdict
    last = defaultdict(lambda: -1)
    left = 0
    best = 0
    for right, c in enumerate(s):
        if last[c] >= left:
            left = last[c] + 1
        last[c] = right
        best = max(best, right - left + 1)
    return best


# Solution 4: Set-based sliding window (O(2n))
def longest_unique_v4(s):
    seen = set()
    left = 0
    best = 0
    for right, c in enumerate(s):
        while c in seen:
            seen.remove(s[left])
            left += 1
        seen.add(c)
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 5: Brute force O(n^2)
def longest_unique_v5(s):
    n = len(s)
    best = 0
    for i in range(n):
        seen = set()
        for j in range(i, n):
            if s[j] in seen:
                break
            seen.add(s[j])
            if j - i + 1 > best:
                best = j - i + 1
    return best


# Solution 6: Two-pointer with counter (>1 means repeat)
def longest_unique_v6(s):
    from collections import Counter
    freq = Counter()
    left = 0
    best = 0
    for right, c in enumerate(s):
        freq[c] += 1
        while freq[c] > 1:
            freq[s[left]] -= 1
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 7: Use a 256-bit bitmap (works for ASCII)
def longest_unique_v7(s):
    # Track which chars are in the current window using a bitmap.
    bitmap = 0
    left = 0
    best = 0
    for right, c in enumerate(s):
        bit = 1 << (ord(c) % 64)  # modulo to handle any char
        while bitmap & bit:
            # Remove s[left]
            bitmap &= ~(1 << (ord(s[left]) % 64))
            left += 1
        bitmap |= bit
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 8: Last-seen as a fixed array of 256 (full ASCII)
def longest_unique_v8(s):
    last = [-1] * 256
    left = 0
    best = 0
    for right, c in enumerate(s):
        idx = ord(c)
        if last[idx] >= left:
            left = last[idx] + 1
        last[idx] = right
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 9: Recursive (iterative over positions)
def longest_unique_v9(s):
    n = len(s)
    last = {}
    best = [0]
    left = [0]

    def helper(right):
        if right == n:
            return
        c = s[right]
        if c in last and last[c] >= left[0]:
            left[0] = last[c] + 1
        last[c] = right
        cur = right - left[0] + 1
        if cur > best[0]:
            best[0] = cur
        helper(right + 1)

    helper(0)
    return best[0]


# Solution 10: Use enumerate + set (Pythonic)
def longest_unique_v10(s):
    seen = set()
    left = 0
    best = 0
    for right, c in enumerate(s):
        if c not in seen:
            seen.add(c)
            best = max(best, right - left + 1)
        else:
            # Shrink from left until c is no longer in window
            while s[left] != c:
                seen.discard(s[left])
                left += 1
            left += 1  # Skip the duplicate c itself
    return best


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (hashmap BEST)",       longest_unique_v1),
        ("V2 (ASCII array)",        longest_unique_v2),
        ("V3 (defaultdict)",        longest_unique_v3),
        ("V4 (set-based)",          longest_unique_v4),
        ("V5 (brute O(n^2))",       longest_unique_v5),
        ("V6 (counter)",            longest_unique_v6),
        ("V7 (bitmap)",             longest_unique_v7),
        ("V8 (256 array)",          longest_unique_v8),
        ("V9 (recursive)",          longest_unique_v9),
        ("V10 (pythonic set)",      longest_unique_v10),
    ]

    test_cases = [
        # (input, expected)
        ("abcabcbb", 3),
        ("bbbbb", 1),
        ("pwwkew", 3),
        ("", 0),
        ("abcdef", 6),
        ("abba", 2),
        ("a", 1),
        ("au", 2),
        ("dvdf", 3),  # "vdf"
        ("tmmzuxt", 5),  # "mzuxt"
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s, expected) in enumerate(test_cases):
            try:
                got = func(s)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: {s!r} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: {s!r} ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")