"""
Isomorphic Strings
Easy | 15 min

Check if two strings are isomorphic. A mapping exists from chars of one
string to chars of the other such that:
- Each char maps to exactly one char (1-to-1)
- Order is preserved

Constraints:
- 0 <= length <= 10^4
- Both strings have same length
- Valid ASCII characters

Examples:
    "egg", "add" -> True (e->a, g->d)
    "foo", "bar" -> True (f->b, o->a)
    "badc", "baba" -> False (b->b AND d->b, two chars to 'b')
    "ab", "aa" -> False (a->a AND b->a, two chars to 'a')
"""

from collections import defaultdict, Counter


# =============================================================================
# WAY 1: Two HashMaps (BEST - Memorize!)
# =============================================================================
# THINKING: "Need 1-to-1 mapping both directions."
def is_isomorphic_1(s, t):
    if len(s) != len(t):
        return False

    s_to_t = {}
    t_to_s = {}

    for c1, c2 in zip(s, t):
        if c1 in s_to_t:
            if s_to_t[c1] != c2:
                return False
        else:
            s_to_t[c1] = c2

        if c2 in t_to_s:
            if t_to_s[c2] != c1:
                return False
        else:
            t_to_s[c2] = c1

    return True


# =============================================================================
# WAY 2: Single HashMap + set
# =============================================================================
def is_isomorphic_2(s, t):
    if len(s) != len(t):
        return False

    mapping = {}
    seen = set()

    for c1, c2 in zip(s, t):
        if c1 in mapping:
            if mapping[c1] != c2:
                return False
        else:
            if c2 in seen:
                return False
            mapping[c1] = c2
            seen.add(c2)

    return True


# =============================================================================
# WAY 3: defaultdict
# =============================================================================
def is_isomorphic_3(s, t):
    if len(s) != len(t):
        return False

    s_to_t = defaultdict(str)
    t_to_s = defaultdict(str)

    for c1, c2 in zip(s, t):
        if s_to_t[c1] and s_to_t[c1] != c2:
            return False
        if t_to_s[c2] and t_to_s[c2] != c1:
            return False
        s_to_t[c1] = c2
        t_to_s[c2] = c1

    return True


# =============================================================================
# WAY 4: Index pattern (clever!)
# =============================================================================
def is_isomorphic_4(s, t):
    return [s.find(c) for c in s] == [t.find(c) for c in t]


# =============================================================================
# WAY 5: Using set comparison
# =============================================================================
def is_isomorphic_5(s, t):
    return len(set(zip(s, t))) == len(set(s)) == len(set(t))


# =============================================================================
# WAY 6: Most compact
# =============================================================================
def is_isomorphic_6(s, t):
    return len(s) == len(t) and len(set(s)) == len(set(t)) == len(set(zip(s, t)))


# =============================================================================
# WAY 7: Using tuple of first indices
# =============================================================================
def is_isomorphic_7(s, t):
    def transform(string):
        return tuple(string.find(c) for c in string)

    return transform(s) == transform(t)


# =============================================================================
# WAY 8: Explicit index loop
# =============================================================================
def is_isomorphic_8(s, t):
    if len(s) != len(t):
        return False

    s_to_t = {}
    t_to_s = {}

    for i in range(len(s)):
        if s[i] in s_to_t:
            if s_to_t[s[i]] != t[i]:
                return False
        else:
            s_to_t[s[i]] = t[i]

        if t[i] in t_to_s:
            if t_to_s[t[i]] != s[i]:
                return False
        else:
            t_to_s[t[i]] = s[i]

    return True


# =============================================================================
# WAY 9: With get default trick
# =============================================================================
def is_isomorphic_9(s, t):
    s_to_t = {}
    t_to_s = {}
    for c1, c2 in zip(s, t):
        if s_to_t.get(c1, c2) != c2 or t_to_s.get(c2, c1) != c1:
            return False
        s_to_t[c1] = c2
        t_to_s[c2] = c1
    return True


# =============================================================================
# WAY 10: With Counter
# =============================================================================
def is_isomorphic_10(s, t):
    if len(s) != len(t):
        return False
    pairs = list(zip(s, t))
    return len(set(pairs)) == len(set(s)) == len(set(t))


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to check if two strings are isomorphic, meaning there's a 1-to-1
mapping between their characters that preserves order."

Key Insight:
"For a valid mapping:
- Each character in s must map to exactly one character in t
- Each character in t must be mapped from exactly one character in s
- This means I need to check BOTH directions"

Algorithm:
"I'll use two hashmaps:
- s_to_t: char in s -> char in t
- t_to_s: char in t -> char in s
For each pair, verify consistency in both directions."

Why both directions:
"If I only check s->t, I might miss the case where two different chars
in s map to the same char in t. Example: 'ab' -> 'aa' would pass s->t
check but is not isomorphic."

Edge cases:
- Different lengths: not isomorphic
- Same string: always isomorphic
- Empty strings: isomorphic

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| HashMaps  | O(n)   | O(n)     |
| Index     | O(n^2) | O(n)     |
| Set       | O(n)   | O(n)     |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two HashMaps", is_isomorphic_1),
        ("Way 2: Single + set", is_isomorphic_2),
        ("Way 3: defaultdict", is_isomorphic_3),
        ("Way 4: Index pattern", is_isomorphic_4),
        ("Way 5: Set comparison", is_isomorphic_5),
        ("Way 6: Most compact", is_isomorphic_6),
        ("Way 7: Tuple indices", is_isomorphic_7),
        ("Way 8: Index loop", is_isomorphic_8),
        ("Way 9: get default", is_isomorphic_9),
        ("Way 10: Counter", is_isomorphic_10),
    ]

    test_cases = [
        ("egg", "add", True),
        ("foo", "bar", True),
        ("badc", "baba", False),
        ("ab", "aa", False),
        ("", "", True),
        ("a", "a", True),
        ("paper", "title", True),
        ("ab", "ca", True),
    ]

    print("=" * 70)
    print("ISOMORPHIC STRINGS - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s, t, expected in test_cases:
            try:
                result = func(s, t)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: '{s}' '{t}' -> {result} (expected {expected})")
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
