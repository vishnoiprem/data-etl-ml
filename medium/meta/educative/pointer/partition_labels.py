"""
Partition Labels
Medium | 30 min

Given a string s, partition it into as many parts as possible so that
each letter appears in at most one part. Return a list of integers
representing the sizes of these partitions.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/partition-labels

Examples:
    "ababcbacadefegdehijhklij" -> [9, 7, 8]
        partitions: "ababcbaca", "defegde", "hijhklij"
    "eccbbbbdec" -> [10]
    "abc" -> [3] (a, b, c each in own)
    "abac" -> [4]  (a and b both span whole string)

Constraints:
- 1 <= s.length <= 500
- s consists of lowercase English letters.

KEY INSIGHT:
Greedy + last-occurrence tracking. We expand the current partition's
right boundary to include the LAST occurrence of any char seen so far.
When i == current_end, partition ends.

Algorithm:
1. last[c] = last index of char c.
2. end = 0, start = 0.
3. For i in 0..n-1:
     end = max(end, last[s[i]]).
     if i == end: append (end - start + 1); start = end + 1.

Time:  O(n) — single pass after building last map.
Space: O(1) — last map has 26 entries.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT PARTITION LABELS:

1. UNDERSTAND THE PROBLEM:
   "Partition s into maximum number of parts where each char appears
   in only ONE part. Return sizes."

2. KEY OBSERVATION:
   "A partition ends when we've passed the LAST occurrence of every
   character seen so far in this partition. Beyond that point, that
   character will not appear again, so we can safely cut here."

3. GREEDY INSIGHT:
   "Maintain 'current partition's rightmost boundary' = max last-occurrence
   of any char seen in this partition.
   When i reaches this boundary, the partition is complete."

4. ALGORITHM:
   1. last[c] = last index of char c in s.  (26 entries)
   2. end = 0; start = 0; result = [].
   3. For i in 0..n-1:
        end = max(end, last[s[i]]).
        if i == end: result.append(end - start + 1); start = end + 1.
   4. Return result.

5. EDGE CASES:
   - Each char unique: n partitions of size 1.
   - All same char: 1 partition of size n.
   - String palindrome: 1 partition.
   - Each char's last occurrence = its first occurrence: n partitions.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Greedy   | O(n)   | O(1)   |
   | Brute    | O(n^2) | O(1)   |
   +----------+--------+--------+

7. WHY GREEDY = OPTIMAL:
   - Cutting earlier would split a char's occurrences.
   - Cutting at the boundary when i == max-end is the EARLIEST safe cut.
   - Earliest safe cut = more partitions later. So greedy maximizes count.
"""


# =============================================================================
# WAY 1: Greedy with last-occurrence map (BEST - Memorize!)
# =============================================================================
def partition_labels_1(s):
    """
    Greedy: track last occurrence of each char.
    Extend partition's right boundary to include last occurrence.
    Cut when i == boundary.
    """
    last = {c: i for i, c in enumerate(s)}
    result = []
    start = end = 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            result.append(end - start + 1)
            start = end + 1
    return result


# =============================================================================
# WAY 2: Greedy with explicit array (26 letters)
# =============================================================================
def partition_labels_2(s):
    """Same as Way 1 but using array index = ord(c) - ord('a')."""
    last = [-1] * 26
    for i, c in enumerate(s):
        last[ord(c) - ord("a")] = i
    result = []
    start = end = 0
    for i, c in enumerate(s):
        end = max(end, last[ord(c) - ord("a")])
        if i == end:
            result.append(end - start + 1)
            start = end + 1
    return result


# =============================================================================
# WAY 3: Greedy with two pointers + last seen
# =============================================================================
def partition_labels_3(s):
    """Two-pointer style. Track max last occurrence so far."""
    last = {c: i for i, c in enumerate(s)}
    left = right = 0
    result = []
    for right in range(len(s)):
        # Update right boundary to include last occurrence of s[right].
        new_right = last[s[right]]
        if new_right > right:
            # Need to extend. Reset end to max.
            pass
        # Recompute end fresh each iteration:
        end = 0
        for j in range(left, right + 1):
            end = max(end, last[s[j]])
        if right == end:
            result.append(right - left + 1)
            left = right + 1
            end = right
    return result


# =============================================================================
# WAY 4: Brute force - try every partition point
# =============================================================================
def partition_labels_4(s):
    """Brute: greedily extend partition until no char appears later."""
    n = len(s)
    result = []
    start = 0
    while start < n:
        # Find smallest end such that no char in s[start..end] appears beyond end.
        end = start
        seen = set()
        while True:
            # Add all chars in current range.
            for i in range(start, end + 1):
                seen.add(s[i])
            # Find max last occurrence of seen chars.
            new_end = end
            for c in seen:
                last = s.rfind(c)
                if last > new_end:
                    new_end = last
            if new_end == end:
                break
            end = new_end
        result.append(end - start + 1)
        start = end + 1
    return result


# =============================================================================
# WAY 5: Greedy with reverse lookup at each step
# =============================================================================
def partition_labels_5(s):
    """Use rfind to get last occurrence dynamically."""
    result = []
    start = 0
    while start < len(s):
        seen = set()
        end = start
        for i in range(start, len(s)):
            seen.add(s[i])
            # Find any char in seen whose last occurrence extends end.
            new_end = end
            for c in seen:
                last = s.rfind(c)
                new_end = max(new_end, last)
            end = new_end
            if i == end:
                break
        result.append(end - start + 1)
        start = end + 1
    return result


# =============================================================================
# WAY 6: Class OOP
# =============================================================================
class PartitionLabels:
    def __init__(self, s):
        self.s = s

    def solve(self):
        last = {c: i for i, c in enumerate(self.s)}
        result = []
        start = end = 0
        for i, c in enumerate(self.s):
            end = max(end, last[c])
            if i == end:
                result.append(end - start + 1)
                start = end + 1
        return result


def partition_labels_6(s):
    return PartitionLabels(s).solve()


# =============================================================================
# WAY 7: Functional with reduce
# =============================================================================
def partition_labels_7(s):
    """Use functools.reduce to accumulate state."""
    from functools import reduce
    last = {c: i for i, c in enumerate(s)}

    def step(state, item):
        i, c = item
        start, end, result = state
        end = max(end, last[c])
        if i == end:
            return (end + 1, end, result + [end - start + 1])
        return (start, end, result)

    _, _, result = reduce(step, enumerate(s), (0, 0, []))
    return result


# =============================================================================
# WAY 8: Greedy with explicit frontier tracking
# =============================================================================
def partition_labels_8(s):
    """
    Alternative: track which indices are 'safe cut points'.
    A position i is safe if no char in s[0..i] appears beyond i.
    """
    last = {c: i for i, c in enumerate(s)}
    n = len(s)
    rightmost = 0
    result = []
    prev_cut = 0
    for i in range(n):
        rightmost = max(rightmost, last[s[i]])
        if i == rightmost:
            result.append(i - prev_cut + 1)
            prev_cut = i + 1
    return result


# =============================================================================
# WAY 9: Greedy with character count technique
# =============================================================================
def partition_labels_9(s):
    """
    Use Counter to count remaining occurrences.
    Decrease as we go. Track count of chars still > 0.
    When that count is 0, partition ends.
    """
    from collections import Counter
    counts = Counter(s)
    result = []
    active = len(counts)  # number of distinct chars with count > 0
    start = 0
    for i, c in enumerate(s):
        counts[c] -= 1
        if counts[c] == 0:
            active -= 1
        if active == 0:
            result.append(i - start + 1)
            start = i + 1
    return result


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def partition_labels_10(s):
    """
    THE ONE TO MEMORIZE.

    Greedy with last-occurrence map.
    - last[c] = last index of char c in s.
    - Walk through. End of current partition = max(last[c] for c in partition).
    - When i == end, append partition length and start a new one.

    Time:  O(n).
    Space: O(1) (26-letter map).
    """
    last = {c: i for i, c in enumerate(s)}
    result = []
    start = end = 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            result.append(end - start + 1)
            start = end + 1
    return result


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Greedy last map (BEST)", partition_labels_1),
        ("Way 2: Greedy array index", partition_labels_2),
        ("Way 3: Two-pointer dynamic", partition_labels_3),
        ("Way 4: Brute force set", partition_labels_4),
        ("Way 5: Greedy rfind", partition_labels_5),
        ("Way 6: Class OOP", partition_labels_6),
        ("Way 7: Functional reduce", partition_labels_7),
        ("Way 8: Frontier tracking", partition_labels_8),
        ("Way 9: Counter technique", partition_labels_9),
        ("Way 10: Final cleanest", partition_labels_10),
    ]

    test_cases = [
        # (s, expected)
        ("ababcbacadefegdehijhklij", [9, 7, 8]),
        ("eccbbbbdec", [10]),
        ("abc", [1, 1, 1]),
        ("abac", [3, 1]),
        ("a", [1]),
        ("aa", [2]),
        ("abcabc", [6]),
        ("abcdef", [1, 1, 1, 1, 1, 1]),
    ]

    print("=" * 70)
    print("PARTITION LABELS - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/partition-labels")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s, expected in test_cases:
            try:
                result = func(s)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: s={s!r}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: s={s!r}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)