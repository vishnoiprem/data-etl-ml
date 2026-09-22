def count_palindromic_substrings(s):
    """
    Count palindromic substrings of s using expand-around-center.
    For each center (single char or gap between two chars), expand
    outward while the substring is a palindrome, incrementing count.
    """
    if not s:
        return 0
    n = len(s)
    count = 0

    def expand(left, right):
        """Expand around (left, right) and count palindromes."""
        c = 0
        while left >= 0 and right < n and s[left] == s[right]:
            c += 1
            left -= 1
            right += 1
        return c

    for center in range(n):
        # Odd-length palindromes (single char center)
        count += expand(center, center)
        # Even-length palindromes (gap center)
        count += expand(center, center + 1)

    return count


if __name__ == "__main__":
    # Test cases
    print(count_palindromic_substrings("abc"))      # 3 (a, b, c)
    print(count_palindromic_substrings("aaa"))      # 6 (a, a, a, aa, aa, aaa)
    print(count_palindromic_substrings("abba"))     # 6 (a, b, b, a, bb, abba)
    print(count_palindromic_substrings("a"))        # 1
    print(count_palindromic_substrings(""))         # 0
    print(count_palindromic_substrings("aba"))      # 4 (a, b, a, aba)
    print(count_palindromic_substrings("ababa"))    # 9
