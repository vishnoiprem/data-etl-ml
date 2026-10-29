"""
Reverse Words in a String - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-words-in-a-string

Given a string sentence with possible leading, trailing, or extra spaces,
reverse the order of words. Words are continuous sequences of non-space
characters. Return a clean string: words separated by single space, no
leading/trailing spaces.

KEY INSIGHT:
Split by whitespace to get the words (handles multiple spaces cleanly),
then join them in reverse with single spaces.

Examples:
    "the sky is blue" -> "blue is sky the"
    "  hello world  " -> "world hello"
    "a good   example" -> "example good a"
    "Bob    Loves  Alice" -> "Alice Loves Bob"

Constraints:
- 1 <= sentence.length <= 10^4
- Contains English letters, digits, and spaces.
- At least one word.
"""

import copy
import re
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: split + reverse + join (BEST - Memorize!)
# ============================================================
def reverse_words_1(sentence):
    """Pythonic: split() handles multiple/leading/trailing spaces automatically."""
    return " ".join(sentence.split()[::-1])


# ============================================================
# Way 2: Manual split with str.strip + str.split
# ============================================================
def reverse_words_2(sentence):
    """Strip and split explicitly."""
    return " ".join(sentence.strip().split()[::-1])


# ============================================================
# Way 3: Two-pointer with manual word extraction
# ============================================================
def reverse_words_3(sentence):
    """Two-pointer scan from end, collecting words. O(n) time, O(n) space."""
    n = len(sentence)
    result = []
    i = n - 1
    while i >= 0:
        # Skip trailing spaces
        while i >= 0 and sentence[i] == ' ':
            i -= 1
        if i < 0:
            break
        # Find start of word
        j = i
        while i >= 0 and sentence[i] != ' ':
            i -= 1
        # sentence[i+1:j+1] is the word
        result.append(sentence[i + 1:j + 1])
    return " ".join(result)


# ============================================================
# Way 4: Reverse whole string, then reverse each word
# ============================================================
def reverse_words_4(sentence):
    """Reverse the whole string, then reverse each word in place.
    Handle extra spaces at the same time."""
    # First, clean up: collapse multiple spaces, strip ends
    cleaned = " ".join(sentence.split())
    # Reverse entire string as list
    chars = list(cleaned)
    chars.reverse()
    # Now reverse each word back
    n = len(chars)
    i = 0
    while i < n:
        start = i
        while i < n and chars[i] != ' ':
            i += 1
        # Reverse chars[start:i]
        chars[start:i] = chars[start:i][::-1]
        i += 1  # skip the space
    return "".join(chars)


# ============================================================
# Way 5: Stack-based word collection
# ============================================================
def reverse_words_5(sentence):
    """Push words onto a stack, pop to reverse."""
    words = sentence.split()
    stack = []
    for w in words:
        stack.append(w)
    result = []
    while stack:
        result.append(stack.pop())
    return " ".join(result)


# ============================================================
# Way 6: regex-based tokenization
# ============================================================
def reverse_words_6(sentence):
    """Use regex to find words, then reverse."""
    words = re.findall(r'\S+', sentence)
    return " ".join(reversed(words))


# ============================================================
# Way 7: Build result by appending to front
# ============================================================
def reverse_words_7(sentence):
    """Iterate words left-to-right; prepend each to result."""
    result = []
    for w in sentence.split():
        result.insert(0, w)
    return " ".join(result)


# ============================================================
# Way 8: Deque-based
# ============================================================
def reverse_words_8(sentence):
    """Use deque.appendleft to build the reversed result."""
    from collections import deque
    dq = deque()
    for w in sentence.split():
        dq.appendleft(w)
    return " ".join(dq)


# ============================================================
# Way 9: Class-based
# ============================================================
class WordReverser_9:
    def __init__(self, sentence):
        self.sentence = sentence

    def reverse(self):
        return " ".join(self.sentence.split()[::-1])


def reverse_words_9(sentence):
    return WordReverser_9(sentence).reverse()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def reverse_words_10(sentence):
    """
    THE ONE TO MEMORIZE.

    The simplest, cleanest approach: split on whitespace (handles multiple
    consecutive spaces, leading/trailing), reverse, join with single space.

    Time:  O(n)
    Space: O(n) for the list of words.
    """
    return " ".join(sentence.split()[::-1])


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reverse the order of words in a string, removing extra
spaces and ensuring single-space separation."

Key Insight:
"Python's str.split() without arguments splits on any whitespace and
discards empty strings, so it handles leading/trailing/multiple spaces
automatically. Then I reverse the list and join with single spaces."

Algorithm:
1. words = sentence.split()  # splits on whitespace, drops empties.
2. Reverse words.
3. Return " ".join(words).

Edge Cases:
- Empty words (only spaces): not allowed (at least one word).
- Single word: returns the same word.
- Leading/trailing spaces: stripped automatically.
- Multiple spaces between words: collapsed to single space.
- Tabs/newlines: also treated as whitespace by split() without args.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| split+join| O(n)   | O(n)   |
| 2-ptr scan| O(n)   | O(n)   |
| Reverse+rev-word| O(n)  | O(n)   |
+-----------+--------+--------+

KEY TRICK:
Use split() WITHOUT arguments — it splits on any whitespace AND discards
empty strings. Don't pass ' ' as the separator; that would create empty
strings from multiple spaces.

RELATED PROBLEMS:
- Reverse Words in a String II (LC 186): in-place on char array.
- Reverse String (LC 344).
- Valid Palindrome (LC 125).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (input, expected, description)
        ("the sky is blue", "blue is sky the", "Standard"),
        ("  hello world  ", "world hello", "Leading/trailing spaces"),
        ("a good   example", "example good a", "Multiple internal spaces"),
        ("Bob    Loves  Alice", "Alice Loves Bob", "Tab-like spacing"),
        ("a", "a", "Single word"),
        ("Hello", "Hello", "Single capitalized word"),
        ("a b c d e", "e d c b a", "Single letter words"),
        ("  single  ", "single", "Padded single word"),
        ("word1 word2", "word2 word1", "With digits"),
        ("  multiple   spaces   here  ", "here spaces multiple", "Many spaces"),
    ]

    implementations = [
        ("Way 1: split+rev+join (BEST)", reverse_words_1),
        ("Way 2: strip+split", reverse_words_2),
        ("Way 3: Two-pointer", reverse_words_3),
        ("Way 4: Reverse whole + each", reverse_words_4),
        ("Way 5: Stack", reverse_words_5),
        ("Way 6: regex", reverse_words_6),
        ("Way 7: Prepend", reverse_words_7),
        ("Way 8: deque", reverse_words_8),
        ("Way 9: Class-based", reverse_words_9),
        ("Way 10: Final cleanest", reverse_words_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for sentence, expected, desc in test_cases:
            try:
                sentence_copy = copy.deepcopy(sentence)
                result = fn(sentence_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={sentence!r} expected={expected!r} got={result!r}")
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
