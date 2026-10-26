"""Valid Palindrome — alphanumeric, case-insensitive.

Time:  O(n)
Space: O(1) extra
"""


def solve_valid_palindrome(s):
    """Return True if ``s`` is a palindrome considering alphanumerics.

    >>> solve_valid_palindrome("A man, a plan, a canal: Panama")
    True
    """
    left, right = 0, len(s) - 1
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
        if s[left].lower() != s[right].lower():
            return False
        left += 1
        right -= 1
    return True


if __name__ == "__main__":
    print(solve_valid_palindrome("A man, a plan, a canal: Panama"))
