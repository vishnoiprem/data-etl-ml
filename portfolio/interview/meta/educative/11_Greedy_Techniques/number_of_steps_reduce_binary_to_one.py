"""
Number of Steps to Reduce Binary Number to 1 - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/number-ofof-steps-to-reduce-binary-number-to-one

Given a binary number as string s, count steps to reduce to 1:
- If even: divide by 2.
- If odd: add 1.

KEY INSIGHT:
Process bits LSB-first. Each LSB==0 is a /2 (no add). Each LSB==1 is +1 with carry.
The total steps = (# of 1-bits above MSB that get carried) + sum of digit positions.
Simpler: count operations directly using integer arithmetic.

Examples:
    "1101" -> 6 (1101=13 -> 1110 -> 111 -> 1000 -> 100 -> 10 -> 1)
    "1" -> 0
    "10" -> 1

Constraints:
- 1 <= s.length <= 10^5
- s consists of '0' and '1' only.
- s[0] == '1' (no leading zeros)
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Integer arithmetic (BEST - Memorize!)
# ============================================================
def num_steps_1(s):
    """Direct integer arithmetic. Count add-1 (odd) and divide-by-2 (shift)."""
    n = int(s, 2)
    steps = 0
    while n > 1:
        if n & 1:
            n += 1
        else:
            n //= 2
        steps += 1
    return steps


# ============================================================
# Way 2: Bit manipulation (count operations on bits)
# ============================================================
def num_steps_2(s):
    """Count bits: each bit-1 except the last contributes an add+carry; each shift is division."""
    steps = 0
    n = int(s, 2)
    carry = 0
    while n > 1:
        if (n & 1) == 1:
            if n == 3 and carry == 0:
                # Special case: 11 -> 100 in 2 steps, not 3
                n = 2
                steps += 2
                continue
            n += 1
            steps += 1
            carry = 1
        else:
            n //= 2
            steps += 1
            carry = 0
    return steps


# ============================================================
# Way 3: Bit counting (direct simulation, no carries - simplified)
# ============================================================
def num_steps_3(s):
    """Direct simulation using bit operations on integer. Clear and concise."""
    n = int(s, 2)
    steps = 0
    while n > 1:
        # Right shift until odd (count divisions), then add 1
        while n & 1 == 0:
            n >>= 1
            steps += 1
        if n == 1:
            break
        n += 1
        steps += 1
    return steps


# ============================================================
# Way 4: Two pointers on string
# ============================================================
def num_steps_4(s):
    """Process bit by bit with carry tracking, count operations."""
    steps = 0
    carry = 0
    # Iterate from right (LSB) to left
    for i in range(len(s) - 1, 0, -1):
        bit = int(s[i]) + carry
        if bit == 1:
            # odd: add 1 (with carry propagation)
            carry = 1
            steps += 2  # add + divide
        elif bit == 0:
            # even: just divide
            steps += 1  # divide
        else:  # bit == 2
            carry = 1
            steps += 1  # divide
    return steps + carry  # final +1 if there's a carry


# ============================================================
# Way 5: Counter-based with carry (deque stores MSB at left)
# ============================================================
def num_steps_5(s):
    """Use a deque where left is MSB. Process by appending 1, then shifting."""
    from collections import deque
    bits = deque(int(c) for c in s)
    steps = 0
    while len(bits) > 1 or bits[0] != 1:
        # The LSB is bits[-1] (rightmost). /2 means removing the rightmost.
        if bits[-1] == 0:
            # even: just pop the right (divide by 2)
            bits.pop()
            steps += 1
        else:
            # odd: add 1 (causes carry from rightmost position)
            i = len(bits) - 1
            while i >= 0 and bits[i] == 1:
                bits[i] = 0
                i -= 1
            if i < 0:
                bits.appendleft(1)
            else:
                bits[i] = 1
            steps += 1
    return steps


# ============================================================
# Way 6: Recursive approach
# ============================================================
def num_steps_6(s):
    """Recursive: if even, 1 + f(n//2); if odd, 1 + f(n+1)."""
    n = int(s, 2)
    if n == 1:
        return 0
    if n & 1:
        return 1 + num_steps_6(bin(n + 1)[2:])
    else:
        return 1 + num_steps_6(bin(n // 2)[2:])


# ============================================================
# Way 7: Class-based
# ============================================================
class BinaryReducer_7:
    def __init__(self, s):
        self.s = s

    def compute(self):
        n = int(self.s, 2)
        steps = 0
        while n > 1:
            if n & 1:
                n += 1
            else:
                n //= 2
            steps += 1
        return steps


def num_steps_7(s):
    return BinaryReducer_7(s).compute()


# ============================================================
# Way 8: With explicit bit operations
# ============================================================
def num_steps_8(s):
    """Use XOR/AND operations for odd/even detection."""
    n = int(s, 2)
    steps = 0
    while n != 1:
        if (n ^ 1) & 1:  # even (LSB = 0)
            n >>= 1
        else:
            n += 1
        steps += 1
    return steps


# ============================================================
# Way 9: Bit counting formula (count 1s in binary representation)
# ============================================================
def num_steps_9(s):
    """Count 1-bits using bit_length of each intermediate value.
    Each leading 1-bit contributes a +1 operation; each digit position contributes a /2.
    """
    n = int(s, 2)
    if n == 1:
        return 0
    # Walk through: each +1 happens when a 1-bit is encountered, each /2 happens
    # per bit position. Simpler: just count operations.
    steps = 0
    cur = n
    while cur > 1:
        if cur & 1:
            cur += 1
            steps += 1
        else:
            cur >>= 1
            steps += 1
    return steps


# ============================================================
# Way 10: Final cleanest
# ============================================================
def num_steps_10(s):
    """Final cleanest version."""
    n = int(s, 2)
    steps = 0
    while n > 1:
        if n & 1:
            n += 1
        else:
            n //= 2
        steps += 1
    return steps


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ("1101", 6, "Standard (13)"),
        ("1", 0, "Single one"),
        ("10", 1, "Two bits (2)"),
        ("1111", 5, "All ones (15)"),
        ("100", 2, "100 (4) -> 10 -> 1"),
        ("110", 4, "110 (6) -> 11 -> 100 -> 10 -> 1"),
        ("101", 5, "101 (5) -> 110 -> 11 -> 100 -> 10 -> 1"),
        ("11110", 6, "11110 (30) -> 1111 -> 10000 -> 1000 -> 100 -> 10 -> 1"),
        ("1000000", 6, "Big number divisible by 2"),
    ]

    implementations = [
        ("Way 1: Int arithmetic (BEST)", num_steps_1),
        ("Way 2: Bit manipulation", num_steps_2),
        ("Way 3: Formula", num_steps_3),
        ("Way 4: Two pointers", num_steps_4),
        ("Way 5: Deque-based", num_steps_5),
        ("Way 6: Recursive", num_steps_6),
        ("Way 7: Class-based", num_steps_7),
        ("Way 8: XOR/AND bits", num_steps_8),
        ("Way 9: Formula variant", num_steps_9),
        ("Way 10: Final cleanest", num_steps_10),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for s, expected, desc in test_cases:
            try:
                s_copy = copy.deepcopy(s)
                result = fn(s_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: s='{s}' expected={expected} got={result}")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
