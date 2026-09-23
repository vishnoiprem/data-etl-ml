"""
Bulls and Cows
Medium | 30 min

Bulls: digits in correct position (same value)
Cows: digits in both secret and guess but different positions

Return hint as "xAyB" where x = bulls, y = cows

Constraints:
- 1 <= secret.length, guess.length <= 10^3
- secret.length == guess.length
- Digits only
- May contain duplicate digits

Examples:
    secret = "1807", guess = "7810" -> "1A3B"
    secret = "1123", guess = "0111" -> "1A1B"
    secret = "1", guess = "0" -> "0A0B"
    secret = "1", guess = "1" -> "1A0B"
"""

from collections import Counter, defaultdict


# =============================================================================
# WAY 1: Two HashMaps (Cleanest - Memorize!)
# =============================================================================
# THINKING: "Count bulls in one pass, then count matching non-bull digits."
def get_hint_1(secret, guess):
    bulls = 0
    secret_count = Counter()
    guess_count = Counter()

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            secret_count[s] += 1
            guess_count[g] += 1

    # Cows = sum of min(counts) for each digit
    cows = sum((secret_count & guess_count).values())

    return f"{bulls}A{cows}B"


# =============================================================================
# WAY 2: Single HashMap with Count Diff
# =============================================================================
def get_hint_2(secret, guess):
    bulls = 0
    cows = 0
    count = {}

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            count[s] = count.get(s, 0) + 1
            count[g] = count.get(g, 0) - 1
            if count[s] <= 0:
                cows += 1
            if count[g] >= 0:
                cows += 1

    return f"{bulls}A{cows // 2}B"


# =============================================================================
# WAY 3: Using DefaultDict
# =============================================================================
def get_hint_3(secret, guess):
    bulls = 0
    secret_count = defaultdict(int)
    guess_count = defaultdict(int)

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            secret_count[s] += 1
            guess_count[g] += 1

    cows = sum(min(secret_count[d], guess_count[d]) for d in secret_count)
    return f"{bulls}A{cows}B"


# =============================================================================
# WAY 4: Array-Based Counting (Fastest)
# =============================================================================
def get_hint_4(secret, guess):
    bulls = 0
    cows = 0
    secret_count = [0] * 10
    guess_count = [0] * 10

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            secret_count[int(s)] += 1
            guess_count[int(g)] += 1

    for i in range(10):
        cows += min(secret_count[i], guess_count[i])

    return f"{bulls}A{cows}B"


# =============================================================================
# WAY 5: One-Pass Optimized (O(n))
# =============================================================================
def get_hint_5(secret, guess):
    bulls = 0
    cows = 0
    count = [0] * 10

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            # If s appeared in guess, it can match (negative means guess has it)
            if count[int(s)] < 0:
                cows += 1
            # If g appeared in secret, it can match (positive means secret has it)
            if count[int(g)] > 0:
                cows += 1
            count[int(s)] += 1
            count[int(g)] -= 1

    return f"{bulls}A{cows}B"


# =============================================================================
# WAY 6: Using Counter Intersection
# =============================================================================
def get_hint_6(secret, guess):
    bulls = sum(1 for s, g in zip(secret, guess) if s == g)

    s_count = Counter()
    g_count = Counter()
    for s, g in zip(secret, guess):
        if s != g:
            s_count[s] += 1
            g_count[g] += 1

    cows = sum((s_count & g_count).values())
    return f"{bulls}A{cows}B"


# =============================================================================
# WAY 7: With Helper Function
# =============================================================================
def get_hint_7(secret, guess):
    def count_dict(s):
        d = {}
        for c in s:
            d[c] = d.get(c, 0) + 1
        return d

    bulls = sum(1 for s, g in zip(secret, guess) if s == g)
    s_dict = count_dict(secret)
    g_dict = count_dict(guess)

    total_matches = sum(min(s_dict.get(d, 0), g_dict.get(d, 0))
                        for d in set(s_dict) | set(g_dict))
    cows = total_matches - bulls

    return f"{bulls}A{cows}B"


# =============================================================================
# WAY 8: Most Compact
# =============================================================================
def get_hint_8(secret, guess):
    s = Counter()
    g = Counter()
    b = 0
    for x, y in zip(secret, guess):
        if x == y:
            b += 1
        else:
            s[x] += 1
            g[y] += 1
    return f"{b}A{sum((s & g).values())}B"


# =============================================================================
# WAY 9: Using List Comprehension
# =============================================================================
def get_hint_9(secret, guess):
    bulls = sum(s == g for s, g in zip(secret, guess))
    non_bull_secret = [s for s, g in zip(secret, guess) if s != g]
    non_bull_guess = [g for s, g in zip(secret, guess) if s != g]
    cows = sum((Counter(non_bull_secret) & Counter(non_bull_guess)).values())
    return f"{bulls}A{cows}B"


# =============================================================================
# WAY 10: One-Pass with Smart Tracking
# =============================================================================
def get_hint_10(secret, guess):
    bulls = 0
    cows = 0
    s_freq = [0] * 10
    g_freq = [0] * 10

    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            s_freq[int(s)] += 1
            g_freq[int(g)] += 1

    # Cows: total matches of non-bull digits
    for i in range(10):
        cows += min(s_freq[i], g_freq[i])

    return f"{bulls}A{cows}B"


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count two things: bulls (same position, same digit) and
cows (digits in both but different positions)."

Approach:
"I'll use a two-pass approach:
1. First pass: count bulls. For non-bulls, track digit frequencies.
2. Second pass: for each digit, the number of cows is min(count in
   secret, count in guess)."

Why this works:
"Bulls are easy - just compare position by position.
Cows are trickier. For each digit, the number of times it appears
in both secret and guess (excluding bulls) is the cow count.
We take min to avoid double counting."

Edge cases:
- All bulls: cows = 0
- All cows: bulls = 0
- Duplicates: handled naturally by Counter
- Single digit: trivial case

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Two maps   | O(n)   | O(1)     |
| Array      | O(n)   | O(1)     |
| One pass   | O(n)   | O(1)     |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two Counter", get_hint_1),
        ("Way 2: Single map diff", get_hint_2),
        ("Way 3: defaultdict", get_hint_3),
        ("Way 4: Array", get_hint_4),
        ("Way 5: One-pass", get_hint_5),
        ("Way 6: Counter &", get_hint_6),
        ("Way 7: Helper", get_hint_7),
        ("Way 8: Compact", get_hint_8),
        ("Way 9: List comp", get_hint_9),
        ("Way 10: Smart track", get_hint_10),
    ]

    test_cases = [
        ("1807", "7810", "1A3B"),
        ("1123", "0111", "1A1B"),
        ("1", "0", "0A0B"),
        ("1", "1", "1A0B"),
        ("1234", "4321", "0A4B"),
        ("1122", "2211", "0A4B"),
        ("1122", "1222", "3A0B"),  # 1 bull (pos 2), no cows
        ("", "", "0A0B"),
    ]

    print("=" * 70)
    print("BULLS AND COWS - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for secret, guess, expected in test_cases:
            try:
                result = func(secret, guess)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: secret='{secret}', guess='{guess}' -> '{result}' (expected '{expected}')")
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
