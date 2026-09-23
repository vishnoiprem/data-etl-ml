"""
Largest Number After Digit Swaps by Parity
Easy | 15 min

You are given a positive integer num. You may swap any two digits of num
that have the same parity (both odd or both even), and you may swap any
digit with any other digit of the same parity.

Return the largest possible integer you can obtain.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/largest-number-after-digit-swaps-by-parity

Examples:
    num = 1234       -> 3412  (swap 1,3 then 2,4)
    num = 65875      -> 87655 (sort even digits, sort odd digits)
    num = 247        -> 427   (swap 2 and 4)
    num = 1324       -> 4213 (1<->3, 2<->4)
    num = 35         -> 53

Constraints:
- 1 <= num <= 10^9

KEY INSIGHT:
Sort digits by parity:
- Collect even digits, sort descending.
- Collect odd digits, sort descending.
- Walk through num. At each position, use the largest available digit
  of the matching parity.

Time:  O(d log d) where d is number of digits.
Space: O(d).
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT LARGEST NUMBER AFTER DIGIT SWAPS BY PARITY:

1. UNDERSTAND THE PROBLEM:
   "Given num, swap digits of same parity to maximize the number.
   Even digits swap with even. Odd digits swap with odd."

2. KEY OBSERVATION:
   "Since any same-parity digits can be swapped freely, we can rearrange
   ALL even digits among themselves, and ALL odd digits among themselves.
   To maximize, place largest even at highest even position, etc."

3. GREEDY INSIGHT:
   "For each position (left to right):
     - If position holds an even digit, place the largest unused even.
     - If position holds an odd digit, place the largest unused odd.
   This gives the lexicographically largest result."

4. ALGORITHM:
   1. Convert num to list of digit chars.
   2. Extract even digits and odd digits.
   3. Sort each descending.
   4. Rebuild: walk through positions, pop from corresponding sorted list.
   5. Join and convert back to int.

5. EDGE CASES:
   - All same parity: just sort digits descending.
   - Single digit: returns same number.
   - Mix: rebuild carefully.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Sort+rebuild | O(d log d) | O(d) |
   | Two heaps | O(d log d) | O(d) |
   +----------+--------+--------+

7. WHY SORT DESCENDING:
   "We use each digit's parity 'budget' once. To maximize, place the
   biggest same-parity digit at the earliest occurrence of that parity."
"""


# =============================================================================
# WAY 1: Sort evens descending, sort odds descending, rebuild (BEST)
# =============================================================================
def largest_number_1(num):
    """
    Best: extract evens and odds, sort descending, rebuild in place.
    """
    digits = list(str(num))
    evens = sorted([d for d in digits if int(d) % 2 == 0], reverse=True)
    odds = sorted([d for d in digits if int(d) % 2 == 1], reverse=True)
    result = []
    even_idx = 0
    odd_idx = 0
    for d in digits:
        if int(d) % 2 == 0:
            result.append(evens[even_idx])
            even_idx += 1
        else:
            result.append(odds[odd_idx])
            odd_idx += 1
    return int("".join(result))


# =============================================================================
# WAY 2: Heap-based (uses heapq with negation for max-heap)
# =============================================================================
def largest_number_2(num):
    """Use max-heaps for evens and odds."""
    import heapq
    even_heap = []
    odd_heap = []
    digits = list(str(num))
    for d in digits:
        if int(d) % 2 == 0:
            heapq.heappush(even_heap, -int(d))
        else:
            heapq.heappush(odd_heap, -int(d))
    result = []
    for d in digits:
        if int(d) % 2 == 0:
            result.append(str(-heapq.heappop(even_heap)))
        else:
            result.append(str(-heapq.heappop(odd_heap)))
    return int("".join(result))


# =============================================================================
# WAY 3: Sort positions, place largest
# =============================================================================
def largest_number_3(num):
    """Sort positions by parity, place largest digits greedily."""
    digits = list(str(num))
    n = len(digits)
    even_positions = [i for i, d in enumerate(digits) if int(d) % 2 == 0]
    odd_positions = [i for i, d in enumerate(digits) if int(d) % 2 == 1]
    even_digits = sorted([int(d) for d in digits if int(d) % 2 == 0], reverse=True)
    odd_digits = sorted([int(d) for d in digits if int(d) % 2 == 1], reverse=True)
    result = [None] * n
    for pos, digit in zip(even_positions, even_digits):
        result[pos] = str(digit)
    for pos, digit in zip(odd_positions, odd_digits):
        result[pos] = str(digit)
    return int("".join(result))


# =============================================================================
# WAY 4: Counter approach
# =============================================================================
def largest_number_4(num):
    """Use Counter to track remaining digits by parity."""
    from collections import Counter
    digits = list(str(num))
    even_counter = Counter(int(d) for d in digits if int(d) % 2 == 0)
    odd_counter = Counter(int(d) for d in digits if int(d) % 2 == 1)
    result = []
    for d in digits:
        parity = int(d) % 2
        target_counter = even_counter if parity == 0 else odd_counter
        # Find largest available digit.
        for candidate in range(9, -1, -1):
            if target_counter[candidate] > 0:
                target_counter[candidate] -= 1
                result.append(str(candidate))
                break
    return int("".join(result))


# =============================================================================
# WAY 5: Selection sort approach (less efficient)
# =============================================================================
def largest_number_5(num):
    """Repeatedly swap to put largest even/odd at each position."""
    digits = list(str(num))
    n = len(digits)
    for i in range(n):
        target_parity = int(digits[i]) % 2
        max_digit = -1
        max_idx = -1
        # Find largest same-parity digit at or after i.
        for j in range(i, n):
            if int(digits[j]) % 2 == target_parity and int(digits[j]) > max_digit:
                max_digit = int(digits[j])
                max_idx = j
        if max_idx > i:
            digits[i], digits[max_idx] = digits[max_idx], digits[i]
    return int("".join(digits))


# =============================================================================
# WAY 6: Sort indices, then place
# =============================================================================
def largest_number_6(num):
    """Sort indices by parity, place largest digits in order."""
    digits = list(str(num))
    n = len(digits)
    even_digits_desc = sorted([d for d in digits if int(d) % 2 == 0], reverse=True)
    odd_digits_desc = sorted([d for d in digits if int(d) % 2 == 1], reverse=True)
    result = [None] * n
    even_i = 0
    odd_i = 0
    for i, d in enumerate(digits):
        if int(d) % 2 == 0:
            result[i] = even_digits_desc[even_i]
            even_i += 1
        else:
            result[i] = odd_digits_desc[odd_i]
            odd_i += 1
    return int("".join(result))


# =============================================================================
# WAY 7: Use deque for FIFO of largest same-parity
# =============================================================================
def largest_number_7(num):
    """Use sorted deques."""
    from collections import deque
    digits = list(str(num))
    evens = deque(sorted([d for d in digits if int(d) % 2 == 0], reverse=True))
    odds = deque(sorted([d for d in digits if int(d) % 2 == 1], reverse=True))
    result = []
    for d in digits:
        if int(d) % 2 == 0:
            result.append(evens.popleft())
        else:
            result.append(odds.popleft())
    return int("".join(result))


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class DigitSwapper:
    def __init__(self, num):
        self.num = num

    def largest(self):
        digits = list(str(self.num))
        evens = sorted([d for d in digits if int(d) % 2 == 0], reverse=True)
        odds = sorted([d for d in digits if int(d) % 2 == 1], reverse=True)
        result = []
        ei = 0
        oi = 0
        for d in digits:
            if int(d) % 2 == 0:
                result.append(evens[ei])
                ei += 1
            else:
                result.append(odds[oi])
                oi += 1
        return int("".join(result))


def largest_number_8(num):
    return DigitSwapper(num).largest()


# =============================================================================
# WAY 9: Functional with map
# =============================================================================
def largest_number_9(num):
    """Use map() to extract digits by parity."""
    digits = list(str(num))
    evens = list(map(str, sorted([int(d) for d in digits if int(d) % 2 == 0], reverse=True)))
    odds = list(map(str, sorted([int(d) for d in digits if int(d) % 2 == 1], reverse=True)))
    result = []
    ei = 0
    oi = 0
    for d in digits:
        if int(d) % 2 == 0:
            result.append(evens[ei])
            ei += 1
        else:
            result.append(odds[oi])
            oi += 1
    return int("".join(result))


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def largest_number_10(num):
    """
    THE ONE TO MEMORIZE.

    Sort evens descending and odds descending.
    Rebuild: at each position, use the largest unused same-parity digit.

    Time:  O(d log d) where d = number of digits.
    Space: O(d).
    """
    digits = list(str(num))
    evens = sorted([d for d in digits if int(d) % 2 == 0], reverse=True)
    odds = sorted([d for d in digits if int(d) % 2 == 1], reverse=True)
    result = []
    ei = 0
    oi = 0
    for d in digits:
        if int(d) % 2 == 0:
            result.append(evens[ei])
            ei += 1
        else:
            result.append(odds[oi])
            oi += 1
    return int("".join(result))


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+rebuild (BEST)", largest_number_1),
        ("Way 2: Heap-based", largest_number_2),
        ("Way 3: Sort positions", largest_number_3),
        ("Way 4: Counter", largest_number_4),
        ("Way 5: Selection sort", largest_number_5),
        ("Way 6: Sort indices", largest_number_6),
        ("Way 7: Deque", largest_number_7),
        ("Way 8: Class OOP", largest_number_8),
        ("Way 9: Functional map", largest_number_9),
        ("Way 10: Final cleanest", largest_number_10),
    ]

    test_cases = [
        # (num, expected)
        (1234, 3412),       # 1,3 swap; 2,4 swap
        (65875, 87655),     # odd: 7,5,5,7,5 -> positions of odds get 7,5,5 then 5,5
        (247, 427),         # 2,4 swap
        (1324, 3142),       # odds: 1,3 -> 3,1; evens: 2,4 -> 4,2
        (35, 53),
        (123, 321),
        (2468, 8642),
        (1357, 7531),
        (1, 1),
        (98, 98),
        (1234567890, 9876543210),  # all odd at odd, all even at even
        (13579, 97531),
        (24680, 86420),
        (12345, 54321),  # odds: 1,3,5 -> 5,3,1 at positions 0,2,4; evens: 2,4 -> 4,2 at 1,3
    ]

    print("=" * 70)
    print("LARGEST NUMBER AFTER DIGIT SWAPS BY PARITY - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/largest-number-after-digit-swaps-by-parity")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for inp, expected in test_cases:
            try:
                result = func(inp)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: num={inp}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: num={inp}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
