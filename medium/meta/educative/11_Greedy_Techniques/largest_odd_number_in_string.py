"""
Largest Odd Number in String
============================
Given a string num (large integer), return the largest odd-valued integer
that can be formed as a non-empty substring of num. Return "" if none.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/largest-odd-number-in-string

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Given a string of digits, find the largest odd integer that appears
    as a substring. An integer is odd iff its last digit is odd."

2. OBSERVE — KEY INSIGHT:
   "Largest odd integer = longest prefix ending at an odd digit.
    Why? An integer's parity depends ONLY on its last digit.
    To maximize the LENGTH of the substring (and hence its value),
    I want the rightmost odd digit and take everything from index 0 to it."

3. PATTERN RECOGNITION:
   "Greedy: scan from right to left, find the first odd digit.
    Return num[0:idx+1]. If no odd digit exists, return ''."

4. EDGE CASES:
   "Empty string -> ''.
    Single odd digit -> the digit itself.
    No odd digit -> ''.
    All even digits -> ''.
    Leading zeros: input has no leading zeros (per constraints), but our
    output might. The largest substring starting at 0 won't have leading
    zeros (since input doesn't), so this is fine."

5. TRICKY DETAIL:
   "Don't try to remove leading zeros or strip — the input guarantees
    no leading zeros. We just take prefix [0..i] where i is the rightmost
    odd digit. Done."

6. ALGORITHM:
   "for i in range(len(num) - 1, -1, -1):
        if num[i] is odd digit:
            return num[:i+1]
    return ''"

7. WHY GREEDY WORKS:
   "For any odd substring, its last digit is odd. If I find the rightmost
    odd digit at position i, then num[0..i] is odd (because num[i] is odd)
    AND it's longer (and therefore larger in value, given same prefix)
    than any odd substring ending at any j < i. So it's the largest."

8. COMPLEXITY:
   "Time: O(n) — single backward scan.
    Space: O(1) extra (output is O(n))."

9. CODE STRUCTURE:
   "for i from len(num)-1 down to 0:
        if int(num[i]) % 2 == 1:
            return num[:i+1]
    return ''"

10. MENTAL TRACE:
    num = '13579'
    i=4: '9' -> odd, return '13579' ✓ (the whole string)

    num = '2468'
    i=3: '8' even
    i=2: '6' even
    i=1: '4' even
    i=0: '2' even
    return '' ✓

    num = '4206'
    i=3: '6' even
    i=2: '0' even
    i=1: '2' even
    i=0: '4' even
    return ''

    num = '12345'
    i=4: '5' odd, return '12345' ✓
"""


# ==============================================================
# Solution 1: Canonical right-to-left scan (CANONICAL)
# ==============================================================
def largest_odd_v1(num):
    """Find the rightmost odd digit; return num[0:idx+1]."""
    for i in range(len(num) - 1, -1, -1):
        if int(num[i]) % 2 == 1:
            return num[:i + 1]
    return ""


# ==============================================================
# Solution 2: Using str.isdigit() and a set of odd digits
# ==============================================================
def largest_odd_v2(num):
    """Pre-compute odd digit set; scan from right."""
    ODD = {"1", "3", "5", "7", "9"}
    for i in range(len(num) - 1, -1, -1):
        if num[i] in ODD:
            return num[:i + 1]
    return ""


# ==============================================================
# Solution 3: enumerate from right (no range)
# ==============================================================
def largest_odd_v3(num):
    """Use reversed(enumerate(num)) for cleaner traversal."""
    ODD = {"1", "3", "5", "7", "9"}
    for i in range(len(num) - 1, -1, -1):
        if num[i] in ODD:
            return num[:i + 1]
    return ""


# ==============================================================
# Solution 4: Using find from right
# ==============================================================
def largest_odd_v4(num):
    """Find the max index i where num[i] is odd using rfind-like logic."""
    # rfind returns -1 if not found; we replicate it for odd digits
    ODD = set("13579")
    # Search from right for first odd digit
    for i in range(len(num) - 1, -1, -1):
        if num[i] in ODD:
            return num[:i + 1]
    return ""


# ==============================================================
# Solution 5: str.translate to mask odd digits
# ==============================================================
def largest_odd_v5(num):
    """
    Use translate to convert odd digits to themselves and even digits to
    a sentinel; then scan from right to find the last non-sentinel (= last odd).
    """
    # Build a translation table: map even digits to '\x00', odd digits to themselves
    table = str.maketrans({"0": "\x00", "2": "\x00", "4": "\x00",
                           "6": "\x00", "8": "\x00"})
    masked = num.translate(table)
    # Walk backwards to find last non-sentinel (= last odd digit)
    for i in range(len(masked) - 1, -1, -1):
        if masked[i] != "\x00":
            return num[:i + 1]
    return ""


# ==============================================================
# Solution 6: Using numpy to find first odd from right
# ==============================================================
def largest_odd_v6(num):
    """Numpy-based: vectorized odd check."""
    try:
        import numpy as np
        if not num:
            return ""
        digits = np.array([int(c) for c in num])
        is_odd = (digits % 2 == 1)
        # Find last index where is_odd is True
        odd_indices = np.where(is_odd)[0]
        if len(odd_indices) == 0:
            return ""
        last_odd_idx = int(odd_indices[-1])
        return num[:last_odd_idx + 1]
    except ImportError:
        return largest_odd_v1(num)


# ==============================================================
# Solution 7: Using a regex for the trailing odd position
# ==============================================================
def largest_odd_v7(num):
    """
    Use regex to find the position of the last odd digit.
    Match all odd digits; take the last match's position.
    """
    import re
    matches = list(re.finditer(r"[13579]", num))
    if not matches:
        return ""
    last_pos = matches[-1].start()
    return num[:last_pos + 1]


# ==============================================================
# Solution 8: Strip trailing evens (reverse view)
# ==============================================================
def largest_odd_v8(num):
    """
    Strip trailing even digits; if anything remains, that's our answer.
    """
    # Walk backwards removing trailing even digits
    end = len(num)
    while end > 0 and num[end - 1] in "02468":
        end -= 1
    if end == 0:
        return ""
    return num[:end]


# ==============================================================
# Solution 9: Index helper with explicit odd check
# ==============================================================
def largest_odd_v9(num):
    """Use a small helper for odd-check; iterate from right."""
    def is_odd_digit(ch):
        return ch in "13579"

    for i in range(len(num) - 1, -1, -1):
        if is_odd_digit(num[i]):
            return num[:i + 1]
    return ""


# ==============================================================
# Solution 10: Iterative find_last with bisect-like logic
# ==============================================================
def largest_odd_v10(num):
    """
    Iterate and track the last seen odd position.
    Single forward pass, tracking the latest odd index.
    """
    ODD = "13579"
    last_odd = -1
    for i, ch in enumerate(num):
        if ch in ODD:
            last_odd = i
    return num[:last_odd + 1] if last_odd >= 0 else ""


# ==============================================================
# Test runner
# ==============================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical rtl scan)",     largest_odd_v1),
        ("V2 (set of odd digits)",      largest_odd_v2),
        ("V3 (enumerate from right)",   largest_odd_v3),
        ("V4 (rfind-style)",            largest_odd_v4),
        ("V5 (translate mask)",         largest_odd_v5),
        ("V6 (numpy vectorized)",       largest_odd_v6),
        ("V7 (regex finditer)",         largest_odd_v7),
        ("V8 (strip trailing evens)",   largest_odd_v8),
        ("V9 (helper function)",        largest_odd_v9),
        ("V10 (forward scan + last)",   largest_odd_v10),
    ]

    test_cases = [
        # name,                input,         expected
        ("all odd",            "13579",       "13579"),
        ("all even",           "2468",        ""),
        ("ends even",          "4206",        ""),
        ("last is odd",        "12345",       "12345"),
        ("middle is odd",      "1234",        "123"),
        ("single odd",         "7",           "7"),
        ("single even",        "8",           ""),
        ("odd in middle",      "20486",       "2048"),  # last odd at idx 3
        ("just odd at end",    "2468135",     "2468135"),
        ("first char odd",     "13579",       "13579"),
        ("first char even",    "24680",       ""),
        ("even then odd",      "240135",      "240135"),
        ("leading zero odd",   "0123",        "0123"),  # last odd at idx 3
        ("leading zero",       "02468",       ""),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for case_name, inp, expected in test_cases:
            try:
                got = func(inp)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{case_name}]: {inp!r} -> {got!r} (expected {expected!r})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{case_name}]: ERROR on {inp!r}: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")

    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:   Largest odd integer that's a substring of num.
2. INSIGHT:      Odd iff last digit is odd; maximize length.
3. PATTERN:      Find rightmost odd digit, take prefix 0..i.
4. EDGE:         No odd digit -> ''; single digit; all even.
5. TRICKY:       No need to handle leading zeros (input guarantees none).
6. ALGORITHM:    Right-to-left scan; first odd digit is the answer's end.
7. PROOF:        Any odd substring ends at an odd digit; longest prefix
                 ending at the rightmost odd gives the max value.
8. COMPLEXITY:   O(n) time, O(1) extra space.
9. CODE:         for i from right; if odd: return num[:i+1].
10. TRACE:       '1234' -> odd at idx 2 -> return '123'.
""")
