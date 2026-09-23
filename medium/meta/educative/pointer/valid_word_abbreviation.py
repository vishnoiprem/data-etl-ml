"""
Valid Word Abbreviation - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/valid-word-abbreviation

Given a string word and an abbreviation abbr, return True if abbr is a valid
abbreviation of word.

An abbreviation replaces non-adjacent, non-empty substrings with their lengths.
- Numeric replacements must NOT have leading zeros.
- "0" alone is invalid (would represent an empty substring).
- Letters must match the corresponding characters in word exactly.
- The abbreviation must fully account for every character in word.

KEY INSIGHT:
Two pointers. When we hit a digit, parse the full number and advance the
word pointer by that amount. When we hit a letter, it must match word[i].
Reject leading zeros and partial matches.

Examples:
    "internationalization", "i12iz4n" -> True (skip 12 chars, then 'i','z', skip 4, 'n')
    "apple", "a2e" -> False (a-p-p-l-e vs a-2skip-e — needs skip 3, not 2)
    "substitution", "s10n" -> True
    "word", "1ord" -> False (leading zeros / 1-skip would need word[0]=='w' false)

Constraints:
- 1 <= word.length <= 20
- word consists of lowercase English letters.
- 1 <= abbr.length <= 10
- abbr consists of lowercase English letters and digits.
- All integers in abbr fit in a 32-bit integer.
"""

import copy
import re
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Two-pointer canonical (BEST - Memorize!)
# ============================================================
def valid_word_abbreviation_1(word, abbr):
    """Two pointers. Parse digit runs and skip; match letters exactly."""
    i, j = 0, 0
    while i < len(word) and j < len(abbr):
        if abbr[j].isdigit():
            # Leading zero check
            if abbr[j] == '0':
                return False
            num = 0
            while j < len(abbr) and abbr[j].isdigit():
                num = num * 10 + int(abbr[j])
                j += 1
            i += num
        else:
            if word[i] != abbr[j]:
                return False
            i += 1
            j += 1
    return i == len(word) and j == len(abbr)


# ============================================================
# Way 2: Regex-based tokenization + two-pointer
# ============================================================
def valid_word_abbreviation_2(word, abbr):
    """Tokenize abbr using regex split, then walk through word with two pointers.
    Reject leading zeros in any digit run."""
    # Validate: no leading zeros in any digit run
    for m in re.finditer(r'\d+', abbr):
        if m.group()[0] == '0':
            return False
    # Tokenize: parts alternates [literal, num, literal, num, ...]
    parts = re.split(r'(\d+)', abbr)
    i = 0
    for k, part in enumerate(parts):
        if not part:
            continue
        if k % 2 == 0:  # literal letters
            if word[i:i + len(part)] != part:
                return False
            i += len(part)
        else:  # number
            i += int(part)
    return i == len(word)


# ============================================================
# Way 3: Regex-based letter-by-letter
# ============================================================
def valid_word_abbreviation_3(word, abbr):
    """Replace each digit run with a placeholder, then walk through."""
    # Pre-check: no leading zeros
    parts = re.split(r'(\d+)', abbr)
    # parts alternates: [literal, num, literal, num, ..., literal]
    i = 0  # index in word
    for k, part in enumerate(parts):
        if not part:
            continue
        if k % 2 == 0:  # literal letters
            for ch in part:
                if i >= len(word) or word[i] != ch:
                    return False
                i += 1
        else:  # number
            if part[0] == '0':
                return False
            i += int(part)
    return i == len(word)


# ============================================================
# Way 4: Two-pointer with explicit state machine
# ============================================================
def valid_word_abbreviation_4(word, abbr):
    """State machine: READ_LETTER or READ_NUMBER."""
    i, j = 0, 0
    state = 'letter'
    num = 0
    while j < len(abbr):
        ch = abbr[j]
        if ch.isdigit():
            if state == 'letter':
                # transition to number
                if ch == '0':
                    return False
                num = 0
                state = 'number'
            num = num * 10 + int(ch)
            j += 1
        else:
            if state == 'number':
                i += num
                num = 0
                state = 'letter'
            if i >= len(word) or word[i] != ch:
                return False
            i += 1
            j += 1
    if state == 'number':
        i += num
    return i == len(word)


# ============================================================
# Way 5: Tokenize then verify
# ============================================================
def valid_word_abbreviation_5(word, abbr):
    """Tokenize abbr into [letter-run, number-run, letter-run, ...] then verify."""
    tokens = []
    j = 0
    while j < len(abbr):
        if abbr[j].isdigit():
            if abbr[j] == '0':
                return False
            num = 0
            while j < len(abbr) and abbr[j].isdigit():
                num = num * 10 + int(abbr[j])
                j += 1
            tokens.append(('num', num))
        else:
            start = j
            while j < len(abbr) and not abbr[j].isdigit():
                j += 1
            tokens.append(('lit', abbr[start:j]))
    # Now verify
    i = 0
    for kind, val in tokens:
        if kind == 'lit':
            if word[i:i + len(val)] != val:
                return False
            i += len(val)
        else:
            i += val
    return i == len(word)


# ============================================================
# Way 6: Two-pointer with separate skip parsing
# ============================================================
def valid_word_abbreviation_6(word, abbr):
    """Same canonical algorithm but structured with separate parsing of skip numbers."""
    i, j = 0, 0
    while i < len(word) and j < len(abbr):
        if abbr[j].isdigit():
            # Leading zero check
            if abbr[j] == '0':
                return False
            # Parse the full number
            num_str = ''
            while j < len(abbr) and abbr[j].isdigit():
                num_str += abbr[j]
                j += 1
            i += int(num_str)
        else:
            if word[i] != abbr[j]:
                return False
            i += 1
            j += 1
    return i == len(word) and j == len(abbr)


# ============================================================
# Way 7: itertools-style chunked
# ============================================================
def valid_word_abbreviation_7(word, abbr):
    """Use groupby to extract runs of digits vs letters, then verify."""
    from itertools import groupby
    # Pre-check: no leading zero
    for is_digit, group in groupby(abbr, key=str.isdigit):
        if is_digit:
            digits = ''.join(group)
            if digits[0] == '0':
                return False
    # Build skip plan: list of (kind, value) where kind in {'L', 'N'}
    plan = []
    for is_digit, group in groupby(abbr, key=str.isdigit):
        chunk = ''.join(group)
        if is_digit:
            plan.append(('N', int(chunk)))
        else:
            plan.append(('L', chunk))
    # Verify
    i = 0
    for kind, val in plan:
        if kind == 'L':
            if word[i:i + len(val)] != val:
                return False
            i += len(val)
        else:
            i += val
    return i == len(word)


# ============================================================
# Way 8: Functional with iterator
# ============================================================
def valid_word_abbreviation_8(word, abbr):
    """Walk using iter(word) and iter(abbr)."""
    wi = iter(range(len(word)))
    ai = iter(range(len(abbr)))
    i = 0
    j = 0
    while j < len(abbr):
        if abbr[j].isdigit():
            if abbr[j] == '0':
                return False
            num = 0
            while j < len(abbr) and abbr[j].isdigit():
                num = num * 10 + int(abbr[j])
                j += 1
            i += num
        else:
            if i >= len(word) or word[i] != abbr[j]:
                return False
            i += 1
            j += 1
    return i == len(word)


# ============================================================
# Way 9: Class-based
# ============================================================
class AbbreviationValidator_9:
    def __init__(self, word, abbr):
        self.word = word
        self.abbr = abbr

    def is_valid(self):
        i, j = 0, 0
        while i < len(self.word) and j < len(self.abbr):
            if self.abbr[j].isdigit():
                if self.abbr[j] == '0':
                    return False
                num = 0
                while j < len(self.abbr) and self.abbr[j].isdigit():
                    num = num * 10 + int(self.abbr[j])
                    j += 1
                i += num
            else:
                if self.word[i] != self.abbr[j]:
                    return False
                i += 1
                j += 1
        return i == len(self.word) and j == len(self.abbr)


def valid_word_abbreviation_9(word, abbr):
    return AbbreviationValidator_9(word, abbr).is_valid()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def valid_word_abbreviation_10(word, abbr):
    """
    THE ONE TO MEMORIZE.

    1. i = j = 0.
    2. While i < len(word) and j < len(abbr):
       a. If abbr[j] is a digit:
          - If abbr[j] == '0': return False (leading zero).
          - Parse the full number from abbr.
          - i += number.
       b. Else (letter):
          - If word[i] != abbr[j]: return False.
          - i += 1, j += 1.
    3. Return i == len(word) and j == len(abbr).

    Time:  O(n + m) where n = len(word), m = len(abbr).
    Space: O(1) extra.
    """
    i, j = 0, 0
    while i < len(word) and j < len(abbr):
        if abbr[j].isdigit():
            if abbr[j] == '0':
                return False
            num = 0
            while j < len(abbr) and abbr[j].isdigit():
                num = num * 10 + int(abbr[j])
                j += 1
            i += num
        else:
            if word[i] != abbr[j]:
                return False
            i += 1
            j += 1
    return i == len(word) and j == len(abbr)


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to check if an abbreviation correctly represents a word, where
numbers in the abbreviation mean 'skip N characters'."

Key Insight:
"Two pointers. When I see a digit, parse the full number and advance the
word pointer by that amount. When I see a letter, it must match the
current word character exactly. Reject leading zeros (e.g., '01')."

Algorithm:
1. i = j = 0.
2. While i < len(word) and j < len(abbr):
   a. If abbr[j] is digit:
      - Leading zero check: abbr[j] == '0' -> False.
      - Parse full number N from abbr (advance j).
      - i += N.
   b. Else: word[i] must equal abbr[j]; i++, j++.
3. Return i == len(word) and j == len(abbr).

Edge Cases:
- Leading zero in number: "01" -> False.
- "0" alone: invalid.
- Empty word or abbr: handled by final equality.
- Numbers larger than remaining word: i will go past len(word); the
  final i == len(word) check fails. (Optionally guard inside.)
- Word with no numbers: just compare directly.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Two-ptr   | O(n+m) | O(1)   |
| Expand    | O(n+m) | O(n+m) |
+-----------+--------+--------+

KEY TRICK:
Parse the FULL digit run before moving the word pointer. A single
`j += 1` per digit would only consume one character of the number.

RELATED PROBLEMS:
- Minimum Length Encoding (LC 820).
- Compare Strings by Frequency (LC 1170).
- String Compression (LC 443): count runs.
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (word, abbr, expected, description)
        ("internationalization", "i12iz4n", True, "Standard"),
        ("apple", "a2e", False, "Wrong skip count"),
        ("substitution", "s10n", True, "Single skip"),
        ("word", "1ord", True, "Skip first char"),
        ("hello", "h5", False, "Skip past end"),
        ("a", "01", False, "Leading zero"),
        ("ab", "a0b", False, "Zero skip"),
        ("ab", "ab", True, "No abbreviation"),
        ("ab", "2", True, "Skip both"),
        ("ab", "1b", True, "Skip one, match b"),
        ("ab", "2b", False, "Skip past end"),
        ("abc", "abc", True, "Identical"),
        ("abc", "abcd", False, "Abbr longer"),
        ("abcd", "abc", False, "Word longer"),
        ("internationalization", "i5a11o1", True, "Multiple skips"),
        ("internationalization", "i18", False, "Skip 18 (too many)"),
        ("internationalization", "i19", True, "Skip 19 (exact)"),
        ("word", "w0rd", False, "Zero inside"),
        ("substitution", "sub4u1", False, "Embedded skip mismatch"),
        ("substitution", "substitution", True, "Full word matches itself"),
    ]

    implementations = [
        ("Way 1: Two-pointer (BEST)", valid_word_abbreviation_1),
        ("Way 2: Regex expand", valid_word_abbreviation_2),
        ("Way 3: Regex split", valid_word_abbreviation_3),
        ("Way 4: State machine", valid_word_abbreviation_4),
        ("Way 5: Tokenize", valid_word_abbreviation_5),
        ("Way 6: Skip with placeholder", valid_word_abbreviation_6),
        ("Way 7: groupby", valid_word_abbreviation_7),
        ("Way 8: Functional iter", valid_word_abbreviation_8),
        ("Way 9: Class-based", valid_word_abbreviation_9),
        ("Way 10: Final cleanest", valid_word_abbreviation_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for word, abbr, expected, desc in test_cases:
            try:
                word_copy = copy.deepcopy(word)
                abbr_copy = copy.deepcopy(abbr)
                result = fn(word_copy, abbr_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: word='{word}' abbr='{abbr}' expected={expected} got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
