def find_tribonacci(n):
    """
    Return the n-th Tribonacci number, defined as:
        T_0 = 0, T_1 = 1, T_2 = 1
        T_n = T_{n-1} + T_{n-2} + T_{n-3}  for n >= 3
    """
    if n == 0:
        return 0
    if n == 1 or n == 2:
        return 1

    # Iterative DP with O(1) space — only need the previous 3 values
    a, b, c = 0, 1, 1  # T_0, T_1, T_2
    for _ in range(3, n + 1):
        a, b, c = b, c, a + b + c
    return c


if __name__ == "__main__":
    # Test cases (small n to verify; n <= 37)
    for i in range(11):
        print(f"T_{i} = {find_tribonacci(i)}")
    # Expected: 0, 1, 1, 2, 4, 7, 13, 24, 44, 81, 149

    print(find_tribonacci(25))   # 1389537
    print(find_tribonacci(37))   # 2082876103 (largest valid)
