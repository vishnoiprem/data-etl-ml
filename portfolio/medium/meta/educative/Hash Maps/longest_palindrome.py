"""
Longest Palindrome
Easy | 15 min

Given a string s of letters, return the length of the longest palindrome
that can be formed using those letters.

Letters are case-sensitive ("Aa" is NOT a palindrome).

Constraints:
- 1 <= s.length <= 10^3
- Lowercase and/or uppercase English letters only

Examples:
    "abccccdd" -> 7 ("dccaccd" or similar)
    "a" -> 1
    "bb" -> 2
    "" -> 0
"""

from collections import Counter, defaultdict


# =============================================================================
# WAY 1: Counter + math (BEST - Memorize!)
# =============================================================================
# THINKING: "Use even counts fully. Add 1 if any odd count exists."
def longest_palindrome_1(s):
    counts = Counter(s)
    length = 0
    odd_found = False

    for count in counts.values():
        if count % 2 == 0:
            length += count
        else:
            length += count - 1  # Take even part
            odd_found = True  # Mark that we can use one for middle

    return length + (1 if odd_found else 0)


# =============================================================================
# WAY 2: Manual dict
# =============================================================================
def longest_palindrome_2(s):
    counts = {}
    for char in s:
        counts[char] = counts.get(char, 0) + 1

    length = 0
    odd_found = False
    for count in counts.values():
        if count % 2 == 0:
            length += count
        else:
            length += count - 1
            odd_found = True

    return length + (1 if odd_found else 0)


# =============================================================================
# WAY 3: Set approach (elegant!)
# =============================================================================
def longest_palindrome_3(s):
    chars = set()
    length = 0

    for char in s:
        if char in chars:
            chars.remove(char)
            length += 2
        else:
            chars.add(char)

    # Add one for the middle if there are leftover chars
    return length + (1 if chars else 0)


# =============================================================================
# WAY 4: defaultdict
# =============================================================================
def longest_palindrome_4(s):
    counts = defaultdict(int)
    for char in s:
        counts[char] += 1

    length = 0
    has_odd = False
    for count in counts.values():
        length += count
        if count % 2 == 1:
            has_odd = True
            length -= 1

    return length + (1 if has_odd else 0)


# =============================================================================
# WAY 5: Bit manipulation style
# =============================================================================
def longest_palindrome_5(s):
    counts = {}
    for char in s:
        counts[char] = counts.get(char, 0) + 1

    total = sum(count // 2 * 2 for count in counts.values())
    has_odd = any(count % 2 == 1 for count in counts.values())
    return total + (1 if has_odd else 0)


# =============================================================================
# WAY 6: Using Counter.most_common
# =============================================================================
def longest_palindrome_6(s):
    counts = Counter(s)
    length = 0
    odd_used = False

    for char, count in counts.items():
        length += count
        if count % 2 == 1:
            if not odd_used:
                odd_used = True  # Keep this one in middle
            else:
                length -= 1

    return length


# =============================================================================
# WAY 7: One-liner
# =============================================================================
def longest_palindrome_7(s):
    counts = Counter(s)
    return sum(count // 2 * 2 for count in counts.values()) + (1 if any(c % 2 for c in counts.values()) else 0)


# =============================================================================
# WAY 8: Most compact
# =============================================================================
def longest_palindrome_8(s):
    c = Counter(s)
    return sum(v - v % 2 for v in c.values()) + any(v % 2 for v in c.values())


# =============================================================================
# WAY 9: Using array (faster)
# =============================================================================
def longest_palindrome_9(s):
    # 52 letters (26 lower + 26 upper)
    counts = [0] * 52

    for char in s:
        if 'a' <= char <= 'z':
            counts[ord(char) - ord('a')] += 1
        else:
            counts[ord(char) - ord('A') + 26] += 1

    length = 0
    has_odd = False
    for count in counts:
        length += count
        if count % 2 == 1:
            has_odd = True
            length -= 1

    return length + (1 if has_odd else 0)


# =============================================================================
# WAY 10: Single pass set
# =============================================================================
def longest_palindrome_10(s):
    odd = set()
    for char in s:
        if char in odd:
            odd.remove(char)
        else:
            odd.add(char)
    # Even chars cancel out, odd chars remain
    return len(s) - len(odd) + (1 if odd else 0)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the longest palindrome that can be formed from the
letters in the string."

Key Insight:
"For a palindrome:
- All even-count characters can be fully used
- One odd-count character can be placed in the middle
- Other odd-count characters contribute (count - 1)"

Algorithm:
"1. Count occurrences of each character (case-sensitive!)
2. For each count, use the even part
3. If any odd count exists, add 1 for the middle"

Why this works:
"A palindrome reads the same forwards and backwards, so characters on
the left must mirror characters on the right. Even counts pair perfectly.
One odd count can sit in the middle."

Edge cases:
- Empty string: 0
- Single character: 1
- All same characters: length of string

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Counter   | O(n)   | O(1)     |
| Set       | O(n)   | O(1)     |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Counter math", longest_palindrome_1),
        ("Way 2: Manual dict", longest_palindrome_2),
        ("Way 3: Set approach", longest_palindrome_3),
        ("Way 4: defaultdict", longest_palindrome_4),
        ("Way 5: Bit manip", longest_palindrome_5),
        ("Way 6: Most common", longest_palindrome_6),
        ("Way 7: One-liner", longest_palindrome_7),
        ("Way 8: Most compact", longest_palindrome_8),
        ("Way 9: Array", longest_palindrome_9),
        ("Way 10: Single set", longest_palindrome_10),
    ]

    test_cases = [
        ("abccccdd", 7),
        ("a", 1),
        ("bb", 2),
        ("AaBb", 4),  # Case sensitive - Aa not allowed but 4 chars total
        ("abc", 1),
        ("aabbcc", 6),
        ("Aa", 1),  # Case sensitive - can't form palindrome from Aa
        ("ccc", 3),
    ]

    print("=" * 70)
    print("LONGEST PALINDROME - ALL 10 IMPLEMENTATIONS")
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
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: '{s}' -> {result} (expected {expected})")
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
