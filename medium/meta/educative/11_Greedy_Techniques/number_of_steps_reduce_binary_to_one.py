def num_steps(str):
    """
    Count steps to reduce a binary number (as string) to 1.
    - Even: divide by 2 (right-shift).
    - Odd: add 1.
    """
    steps = 0
    # Work with a list of ints; reverse so LSB is at index 0.
    digits = [int(c) for c in str[::-1]]

    # Loop until the number equals 1 (single digit '1').
    while len(digits) > 1 or digits[0] != 1:
        if digits[0] == 0:
            # Even (LSB == 0): divide by 2 (right-shift). Drop the LSB.
            digits.pop(0)
        else:
            # Odd (LSB == 1): add 1. Propagate carry.
            i = 0
            while i < len(digits) and digits[i] == 1:
                digits[i] = 0
                i += 1
            if i == len(digits):
                digits.append(1)
            else:
                digits[i] += 1
        steps += 1

    return steps


if __name__ == "__main__":
    # Test cases
    print(num_steps("1101"))     # 1101(13) -> 1110 -> 111 -> 1000 -> 100 -> 10 -> 1 = 6
    print(num_steps("10"))        # 10(2) -> 1 = 1
    print(num_steps("1"))         # 1 = 0
    print(num_steps("1111"))      # 15: 1111 -> 10000 -> 1000 -> 100 -> 10 -> 1 = 5
    print(num_steps("100"))       # 4: 100 -> 10 -> 1 = 2
