"""Word Break II — every sentence that the dictionary can produce.

Time:  O(n · 2^n) worst case — many splits
Space: O(n)
"""


def solve_word_break_ii(s, word_dict):
    """Return every segmentation of s into words.

    >>> sorted(solve_word_break_ii("catsanddog", ["cat","cats","and","sand","dog"]))
    ['cat sand dog', 'cats and dog']
    """
    word_set = set(word_dict)
    out = []

    def backtrack(start, current):
        if start == len(s):
            out.append(" ".join(current))
            return
        for end in range(start + 1, len(s) + 1):
            word = s[start:end]
            if word in word_set:
                current.append(word)
                backtrack(end, current)
                current.pop()

    backtrack(0, [])
    return out


if __name__ == "__main__":
    print(solve_word_break_ii("catsanddog", ["cat", "cats", "and", "sand", "dog"]))
