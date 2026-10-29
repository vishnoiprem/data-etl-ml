"""
Custom Sort String
Medium | 30 min

Given two strings, order and s, return any permutation of s where:
- Characters appear in the same relative order as in `order`
- If x appears before y in order, x must appear before y in result

Constraints:
- 1 <= order.length <= 26
- 1 <= s.length <= 200
- Lowercase English letters
- All chars in order are unique

Examples:
    order = "cba", s = "abcd" -> "cbad" (or any valid permutation)
    order = "xyz", s = "xyz"  -> "xyz"
    order = "abc", s = "cba"  -> "abc"
"""

from collections import Counter, defaultdict


# =============================================================================
# WAY 1: Counter + Loop (BEST - Memorize!)
# =============================================================================
# THINKING: "Two-pass: 1) Output chars in order, 2) Output rest."
def custom_sort_string_1(order, s):
    count = Counter(s)
    result = []

    # First: chars that appear in order (in the right sequence)
    for char in order:
        if char in count:
            result.append(char * count[char])
            del count[char]

    # Then: remaining chars (not in order)
    for char in count:
        result.append(char * count[char])

    return "".join(result)


# =============================================================================
# WAY 2: Dict + Loop
# =============================================================================
def custom_sort_string_2(order, s):
    count = {}
    for c in s:
        count[c] = count.get(c, 0) + 1

    result = []
    for c in order:
        if c in count:
            result.append(c * count[c])
            del count[c]

    for c in count:
        result.append(c * count[c])

    return "".join(result)


# =============================================================================
# WAY 3: defaultdict
# =============================================================================
def custom_sort_string_3(order, s):
    count = defaultdict(int)
    for c in s:
        count[c] += 1

    result = []
    seen = set()

    for c in order:
        if c in count:
            result.append(c * count[c])
            seen.add(c)

    for c in count:
        if c not in seen:
            result.append(c * count[c])

    return "".join(result)


# =============================================================================
# WAY 4: One-Liner
# =============================================================================
def custom_sort_string_4(order, s):
    c = Counter(s)
    return "".join(ch * c.pop(ch, 0) for ch in order) + "".join(ch * cnt for ch, cnt in c.items())


# =============================================================================
# WAY 5: Custom Sort Key
# =============================================================================
def custom_sort_string_5(order, s):
    # Map each char in order to its position; chars not in order get large values
    order_map = {c: i for i, c in enumerate(order)}
    return "".join(sorted(s, key=lambda c: order_map.get(c, ord(c))))


# =============================================================================
# WAY 6: List-based Counting
# =============================================================================
def custom_sort_string_6(order, s):
    # 26 lowercase letters, use array
    count = [0] * 26
    for c in s:
        count[ord(c) - ord('a')] += 1

    result = []
    for c in order:
        idx = ord(c) - ord('a')
        result.append(c * count[idx])
        count[idx] = 0

    # Remaining chars
    for i in range(26):
        if count[i] > 0:
            result.append(chr(ord('a') + i) * count[i])

    return "".join(result)


# =============================================================================
# WAY 7: Most Compact
# =============================================================================
def custom_sort_string_7(order, s):
    count = Counter(s)
    out = "".join(c * count.pop(c, 0) for c in order)
    return out + "".join(c * n for c, n in count.items())


# =============================================================================
# WAY 8: With string builder list
# =============================================================================
def custom_sort_string_8(order, s):
    count = Counter(s)
    parts = []

    for c in order:
        if count[c]:
            parts.append(c * count[c])
            count[c] = 0

    for c, n in count.items():
        if n:
            parts.append(c * n)

    return "".join(parts)


# =============================================================================
# WAY 9: In-Place Modification of list
# =============================================================================
def custom_sort_string_9(order, s):
    count = Counter(s)
    s_list = list(s)

    # Place chars in order
    idx = 0
    for c in order:
        while count[c] > 0:
            s_list[idx] = c
            count[c] -= 1
            idx += 1

    # Place remaining chars (preserve their relative order from s)
    seen = set(order)
    for c in s:
        if c not in seen:
            s_list[idx] = c
            idx += 1

    return "".join(s_list)


# =============================================================================
# WAY 10: Functional with reduce
# =============================================================================
from functools import reduce


def custom_sort_string_10(order, s):
    count = Counter(s)

    def add_char(acc, c):
        return acc + c * count.pop(c, 0)

    ordered_part = reduce(add_char, order, "")
    rest_part = "".join(c * n for c, n in count.items())
    return ordered_part + rest_part


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reorder s so that characters follow the order in the 'order' string.
Any characters in s that aren't in 'order' can go anywhere - typically at the end."

Approach:
"I'll use a two-pass approach. First, I'll count occurrences of each char in s
using a hashmap. Then I'll iterate through 'order' and add each character (as many
times as it appears in s) to the result. Finally, I'll add any remaining chars
that weren't in 'order'."

Why this works:
"Since I'm iterating through 'order' first, characters in the result appear in the
correct relative order. The remaining chars at the end can be in any order."

Alternative:
"I could also use Python's sorted() with a custom key that maps each char to its
position in 'order'. This is more elegant but less obvious."

EDGE CASES:
- What if a char in 'order' doesn't appear in s? Skip it (count is 0).
- What if all chars in s are in 'order'? Just output in order.
- What if no chars in 'order' appear in s? Return s as-is.

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Counter   | O(n)   | O(1)     |
| Sort key  | O(nlogn)| O(n)   |
+-----------+--------+----------+
where n = len(s)
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Counter loop", custom_sort_string_1),
        ("Way 2: Dict loop", custom_sort_string_2),
        ("Way 3: defaultdict", custom_sort_string_3),
        ("Way 4: One-liner", custom_sort_string_4),
        ("Way 5: Sort key", custom_sort_string_5),
        ("Way 6: Array count", custom_sort_string_6),
        ("Way 7: Compact", custom_sort_string_7),
        ("Way 8: String builder", custom_sort_string_8),
        ("Way 9: In-place", custom_sort_string_9),
        ("Way 10: Reduce", custom_sort_string_10),
    ]

    test_cases = [
        ("cba", "abcd", ["cbad", "cbda"]),  # Multiple valid outputs
        ("xyz", "xyz", ["xyz"]),
        ("abc", "cba", ["abc"]),
        ("kqep", "pekeq", ["kqeep", "kqeee", "kqeeq".replace("eq", "ke"), "kqeep"]),
    ]

    def is_valid(order, s, result):
        """Check if result follows the custom order constraint."""
        if sorted(result) != sorted(s):
            return False
        # Check relative order
        last_pos = -1
        for c in order:
            if c not in s:
                continue
            for i, ch in enumerate(result):
                if ch == c:
                    if i < last_pos:
                        return False
                    last_pos = i
                    break
        return True

    print("=" * 70)
    print("CUSTOM SORT STRING - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for order, s, expected in test_cases:
            try:
                result = func(order, s)
                valid = is_valid(order, s, result)
                # Check if it's one of the expected valid outputs or valid
                passes = valid and sorted(result) == sorted(s)
                if not passes:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if passes else "✗"
                print(f"  {status} {name}: order='{order}', s='{s}' -> '{result}'")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR - {e}")
        print(f"  Overall: {'PASS' if all_test_pass else 'FAIL'}\n")

    print("=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
