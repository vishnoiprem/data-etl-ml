"""
Minimum Window Subsequence - 10 Ways
====================================
Given strings s1 and s2, return the minimum (shortest) substring of s1
such that s2 is a subsequence of that substring.

If there is no such substring in s1, return "".

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-window-subsequence
          (LeetCode #727)

Examples:
    s1 = "abcdebdde", s2 = "bde"   -> "bcde"  ("bcde" contains "bde" as subsequence)
    s1 = "jmeqksfrs", s2 = "mek"   -> ""      (no subsequence)
    s1 = "abc", s2 = "abc"         -> "abc"
    s1 = "abc", s2 = "acb"         -> ""

Constraints:
- 0 <= s1.length <= 10^4 (some variants)
- 0 <= s2.length <= 10^4
- s1 and s2 consist of lowercase English letters.

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find the shortest substring of s1 that contains s2 as a subsequence."

2. KEY INSIGHT:
   "Two-pointer scan. For each position of s1 where s2[0] matches, scan
    forward to find a window containing all of s2. Then move the start
    forward as much as possible while keeping s2 as a subsequence."

3. PATTERN RECOGNITION:
   "For each 'start' in s1 that matches s2[0], do:
    - advance_end: scan forward to find a window where s2 is a subsequence.
    - advance_start: move start forward greedily.
    - Update best."

4. EDGE CASES:
   - s2 longer than s1 -> "".
   - s2 == "" -> "" (often constraint says length >= 1).
   - s1 == s2 -> s1.
   - No subsequence at all -> "".

5. TRICKY DETAIL:
   "When scanning for s2 as subsequence, we want the SHORTEST such
    window. We use 'advance_start' to skip s2[0] chars from the start
    while still maintaining s2 as subsequence of s1[start..end]."

6. ALGORITHM:
   "best = ''
    i = 0
    while i < len(s1):
        if s1[i] != s2[0]: i += 1; continue
        # Try to find end
        j = i; k = 0
        while j < len(s1) and k < len(s2):
            if s1[j] == s2[k]: k += 1
            j += 1
        if k == len(s2):
            # Found window [i..j-1]. Now greedily shrink start.
            end = j - 1
            start = i
            k = len(s2) - 1
            while k >= 0 and start <= end:
                if s1[start] == s2[k]: k -= 1
                start += 1
            start -= 1  # back up to last match
            # Window is s1[start..end]
            window = s1[start:end + 1]
            if not best or len(window) < len(best):
                best = window
            i = start + 1  # Move past start to find next
        else:
            break
    return best"

7. WHY IT WORKS:
   "For each position i in s1 that matches s2[0], we find the
    shortest window containing s2 as subsequence. We track the
    minimum. Once we've exhausted all start positions, return min."

8. COMPLEXITY:
   "Time: O(n*m) where n=len(s1), m=len(s2). Worst case: each
    forward scan is O(n), advance_start is O(m), and we may do this
    O(n) times."
   "Space: O(1) for indices, O(n) for the resulting substring."

9. CODE STRUCTURE:
   "Outer loop over start positions. For each start that matches s2[0],
    do forward scan then greedy shrink. Update best."

10. MENTAL TRACE:
    s1 = "abcdebdde", s2 = "bde":
    i=0 'a': no match. i=1.
    i=1 'b': matches s2[0]='b'.
      Forward scan: j=1,k=0. s1[1]='b'=s2[0]='b', k=1. j=2.
        s1[2]='c',s2[1]='d'. j=3.
        s1[3]='d'=s2[1]='d', k=2. j=4.
        s1[4]='e'=s2[2]='e', k=3. j=5.
      k==3, found end at j-1=4.
      Greedy shrink: k=2,s2[2]='e'. start=1, s1[1]='b'!=e. start=2.
        start=2, s1[2]='c'!=e. start=3.
        start=3, s1[3]='d'!=e. start=4.
        start=4, s1[4]='e'=e, k=1. start=5.
        k=1, s2[1]='d'. start=5>end=4. stop.
      Window = s1[4..4] = "e" len 1. But that doesn't contain "bde"!
      Wait, I think I have an off-by-one. Let me re-check.
      Actually start was incremented past the match. After s1[4]=e matches,
      start=5. Then we exit because start > end.
      So window = s1[start..end] where start=4, end=4 (back up).
      But that's just 'e', which doesn't have 'b' or 'd'.

    Hmm, the algorithm should be: after advancing start, the start
    should be the position of the LAST char matched (which is s2[k]).
    Let me re-derive:
      start=1, k=2 (s2[2]='e'). Scan backwards: at start=4, s1[4]='e'=s2[2], so k=1. start=5.
      But we need to remember that the match was at start=4.
      So actual window start is 4 (the match position).
      But end was 4. So window = "e" len 1.

    Hmm this is too aggressive. The greedy shrink should advance start
    until the match is lost. So actually we need start to be the
    LATEST position where the i-th char of s2 matched.

    Let me redo:
      advance_start: scan backwards from end. k = len(s2) - 1.
      For each char in window from end to start:
        if char == s2[k]: k -= 1; remember position
      The new start is the position of s2[0] match.
      This is the LAST possible s2[0] that still allows subsequence.

    Actually the standard algorithm:
      After forward scan finds j-1 as end (window [i..j-1] covers s2),
      we greedily shrink start:
        k = len(s2) - 1
        end_idx = j - 1
        start_idx = j - 1
        while k >= 0:
          if s1[start_idx] == s2[k]:
            k -= 1
            if k < 0: break
          start_idx -= 1
        # After loop, start_idx is one before s2[0] match.
        # Actually s1[start_idx+1] should be s2[0].
        # Wait, I had k=2 (last char). I need to find s2[2] first.

    Let me re-derive the standard greedy shrink:
      We want the smallest window [start, end] such that s2 is a
      subsequence of s1[start..end]. We know s1[i..j-1] is one such
      window. To shrink:
        1. Find the LAST occurrence of s2[len(s2)-1] in [i..j-1].
           Call this end_pos.
        2. Find the LAST occurrence of s2[len(s2)-2] in [i..end_pos-1].
           ...
        3. The smallest start is the position of s2[0] after this scan.
      After shrinking, window is [s2[0]_pos..end_pos].

    For "abcdebdde", s2="bde":
      Forward scan from i=1: j=5, end_pos=4 ('e').
      Now find last 'd' (s2[1]) in [1..4-1] = [1..3]: positions 1,2,3
        (chars: b,c,d). Last 'd' is at 3.
      Now find last 'b' (s2[0]) in [1..3-1] = [1..2]: chars b,c. 'b' at 1.
      Window = s1[1..4] = "bcde" len 4. ✓

    So the algorithm is correct, I just had the direction wrong.
    Let me write the canonical version correctly:

    i = 0
    while i < len(s1):
      if s1[i] != s2[0]: i += 1; continue
      # Forward scan
      j = i; k = 0
      while j < len(s1) and k < len(s2):
        if s1[j] == s2[k]: k += 1
        j += 1
      if k < len(s2): break
      end_pos = j - 1
      # Greedy shrink: walk back from end, finding s2 chars from end to start
      k = len(s2) - 1
      start_pos = end_pos
      while k >= 0 and start_pos >= i:
        if s1[start_pos] == s2[k]:
          k -= 1
        start_pos -= 1
      start_pos += 1  # back up to last matched position
      # Update best
      window = s1[start_pos:end_pos + 1]
      if not best or len(window) < len(best):
        best = window
      i = start_pos + 1
    return best
"""


# Solution 1: Forward scan + greedy shrink (BEST)
def min_window_subseq_v1(s1, s2):
    if not s1 or not s2 or len(s2) > len(s1):
        return ""
    best = ""
    i = 0
    while i < len(s1):
        if s1[i] != s2[0]:
            i += 1
            continue
        # Forward scan: find smallest end covering s2 as subsequence
        j = i
        k = 0
        while j < len(s1) and k < len(s2):
            if s1[j] == s2[k]:
                k += 1
            j += 1
        if k < len(s2):
            break
        end_pos = j - 1
        # Greedy shrink: find smallest start
        k = len(s2) - 1
        start_pos = end_pos
        while k >= 0 and start_pos >= i:
            if s1[start_pos] == s2[k]:
                k -= 1
            start_pos -= 1
        start_pos += 1
        window = s1[start_pos:end_pos + 1]
        if not best or len(window) < len(best):
            best = window
        i = start_pos + 1
    return best


# Solution 2: For each start, scan forward, then greedy shrink (clean)
def min_window_subseq_v2(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    best = ""
    for i in range(n):
        if s1[i] != s2[0]:
            continue
        # Scan forward
        j = i
        k = 0
        while j < n and k < m:
            if s1[j] == s2[k]:
                k += 1
            j += 1
        if k < m:
            continue
        # Greedy shrink from end
        end = j - 1
        start = end
        k = m - 1
        while k >= 0:
            if s1[start] == s2[k]:
                k -= 1
            if k >= 0:
                start -= 1
        window = s1[start:end + 1]
        if not best or len(window) < len(best):
            best = window
    return best


# Solution 3: DP (forward pass to find earliest end)
def min_window_subseq_v3(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    # For each (i, j) position in s1, what's the earliest index in s1
    # where s2[0..j] matches as subsequence of s1[i..end]?
    # Actually let's use a different DP:
    # dp[j] = earliest end in s1 (as of current start) for s2[0..j]
    best = ""
    for i in range(n):
        if s1[i] != s2[0]:
            continue
        # dp[j] = index in s1 where s2[j] is matched
        dp = [-1] * m
        k = 0
        for j in range(i, n):
            if k < m and s1[j] == s2[k]:
                dp[k] = j
                k += 1
                if k == m:
                    break
        if k < m:
            continue
        # Greedy shrink
        end = dp[m - 1]
        start = end
        k = m - 1
        while k >= 0:
            if s1[start] == s2[k]:
                k -= 1
            if k >= 0:
                start -= 1
        window = s1[start:end + 1]
        if not best or len(window) < len(best):
            best = window
    return best


# Solution 4: DP from end (more efficient)
def min_window_subseq_v4(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    # dp[i][j] = shortest window starting at s1[i] for s2[j..]
    # Fill from bottom-right.
    # Actually use a different DP:
    # match[i][j] = smallest end index in s1 where s2[j..] can be matched
    # starting from s1[i].
    INF = float('inf')
    # match[i][j] = smallest end index of s1 where s2[j..] can be a
    # subsequence of s1[i..end]
    match = [[INF] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        match[i][m] = i  # empty s2 matches at any position
    # Fill from bottom-right
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if s1[i] == s2[j]:
                match[i][j] = match[i + 1][j + 1]
            else:
                match[i][j] = match[i + 1][j]
    # Now for each i where s1[i] matches s2[0], find window length.
    best = ""
    for i in range(n):
        if s1[i] == s2[0] and match[i + 1][1] < INF:
            end = match[i + 1][1] - 1
            window = s1[i:end + 1]
            if not best or len(window) < len(best):
                best = window
    return best


# Solution 5: Two-pointer with rescan
def min_window_subseq_v5(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    best = ""
    i = 0
    while i < n:
        if s1[i] != s2[0]:
            i += 1
            continue
        # Find earliest end
        j = i
        k = 0
        while j < n and k < m:
            if s1[j] == s2[k]:
                k += 1
            j += 1
        if k < m:
            break
        end = j - 1
        # Find latest start
        start = end
        k = m - 1
        while k >= 0:
            if s1[start] == s2[k]:
                k -= 1
            start -= 1
        start += 1
        window = s1[start:end + 1]
        if not best or len(window) < len(best):
            best = window
        i = start + 1
    return best


# Solution 6: Brute force O(n^2)
def min_window_subseq_v6(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    best = ""

    def is_subseq(s, t):
        # Is t a subsequence of s?
        i = 0
        for c in s:
            if i < len(t) and c == t[i]:
                i += 1
        return i == len(t)

    for i in range(n):
        for j in range(i + m - 1, n):
            if is_subseq(s1[i:j + 1], s2):
                if not best or (j - i + 1) < len(best):
                    best = s1[i:j + 1]
                break  # Found shortest ending at j (since we go i..j)
    return best


# Solution 7: Recursive
def min_window_subseq_v7(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""

    def find_end(start):
        k = 0
        j = start
        while j < n and k < m:
            if s1[j] == s2[k]:
                k += 1
            j += 1
        return j - 1 if k == m else -1

    def find_start(end):
        # Find largest start <= end such that s2 is subsequence of
        # s1[start..end]. Walk back from end, matching s2 chars from
        # last to first.
        k = m - 1
        start = end
        while k >= 0 and start >= 0:
            if s1[start] == s2[k]:
                k -= 1
            start -= 1
        # After loop: start is one BEFORE the position of s2[0] match
        # (or it has gone past it).
        return start + 1 if k < 0 else -1

    best = [""]

    def helper(i):
        if i >= n:
            return
        if s1[i] != s2[0]:
            helper(i + 1)
            return
        end = find_end(i)
        if end < 0:
            return
        start = find_start(end)
        window = s1[start:end + 1]
        if not best[0] or len(window) < len(best[0]):
            best[0] = window
        helper(start + 1)

    helper(0)
    return best[0]


# Solution 8: Two-pointer without greedy shrink (slower but simpler)
def min_window_subseq_v8(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    best = ""
    for i in range(n):
        if s1[i] != s2[0]:
            continue
        # Forward scan
        j = i
        k = 0
        while j < n and k < m:
            if s1[j] == s2[k]:
                k += 1
            j += 1
        if k < m:
            continue
        end = j - 1
        # Don't shrink; just use [i..end]
        window = s1[i:end + 1]
        if not best or len(window) < len(best):
            best = window
    return best


# Solution 9: For each end position, find earliest start
def min_window_subseq_v9(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    best = ""

    def earliest_start_with_subseq(end, s2_pos):
        # Starting from end, walk back to find s2 chars from end.
        nonlocal_match_pos = end
        k = m - 1
        i = end
        while k >= 0 and i >= 0:
            if s1[i] == s2[k]:
                k -= 1
            i -= 1
        return i + 1 if k < 0 else -1

    # Find all end positions where s2 is subsequence ending there
    for end in range(n):
        # Walk back from end, try to find s2 as subsequence
        k = m - 1
        i = end
        while k >= 0 and i >= 0:
            if s1[i] == s2[k]:
                k -= 1
            i -= 1
        if k < 0:
            start = i + 1
            window = s1[start:end + 1]
            if not best or len(window) < len(best):
                best = window
    return best


# Solution 10: Cleaner two-pointer with one-pass
def min_window_subseq_v10(s1, s2):
    n, m = len(s1), len(s2)
    if not s1 or not s2 or m > n:
        return ""
    best = ""
    i = 0
    while i < n:
        # Find next match of s2[0]
        while i < n and s1[i] != s2[0]:
            i += 1
        if i >= n:
            break
        # Forward scan
        j = i + 1
        k = 1
        while j < n and k < m:
            if s1[j] == s2[k]:
                k += 1
            j += 1
        if k < m:
            break
        end = j - 1
        # Greedy shrink
        start = end
        k = m - 1
        while k >= 0 and start >= i:
            if s1[start] == s2[k]:
                k -= 1
            start -= 1
        start += 1
        window = s1[start:end + 1]
        if not best or len(window) < len(best):
            best = window
        i = start + 1
    return best


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                  min_window_subseq_v1),
        ("V2 (clean)",                 min_window_subseq_v2),
        ("V3 (DP forward)",            min_window_subseq_v3),
        ("V4 (DP from end)",           min_window_subseq_v4),
        ("V5 (two-pointer)",           min_window_subseq_v5),
        ("V6 (brute)",                 min_window_subseq_v6),
        ("V7 (recursive)",             min_window_subseq_v7),
        ("V8 (no shrink)",             min_window_subseq_v8),
        ("V9 (per-end scan)",          min_window_subseq_v9),
        ("V10 (one-pass)",             min_window_subseq_v10),
    ]

    test_cases = [
        # (s1, s2, expected)
        ("abcdebdde", "bde", "bcde"),
        ("jmeqksfrs", "mek", "meqk"),  # m at 1, e at 2, k at 4 -> "meqk" len 4
        ("abc", "abc", "abc"),
        ("abc", "acb", ""),  # acb is NOT a subsequence of "abc"
        ("abc", "", ""),
        ("", "abc", ""),
        ("a", "a", "a"),
        ("aaab", "ab", "ab"),
        ("cabbcbacba", "abc", "abbc"),  # a=1,b=2,c=4 -> "abbc" len 4
        ("cnfbcddyha", "cdy", "cddy"),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s1, s2, expected) in enumerate(test_cases):
            try:
                got = func(s1, s2)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: s1={s1!r}, s2={s2!r} -> {got!r} (expected {expected!r})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")