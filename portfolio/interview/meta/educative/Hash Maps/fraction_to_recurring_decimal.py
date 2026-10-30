"""
Fraction to Recurring Decimal
Medium | 30 min

Given numerator and denominator, return fraction as string.
If decimal part repeats, enclose repeating part in parentheses.

Examples:
    1/2   -> "0.5"
    2/3   -> "0.(6)"
    1/6   -> "0.1(6)"
    -50/8 -> "-6.25"
    -1/2  -> "-0.5"

Constraints:
- denominator != 0
- -10^5 <= numerator, denominator <= 10^5 - 1
"""


# =============================================================================
# WAY 1: Basic HashMap Approach
# =============================================================================
# THINKING: "Long division with hashmap to track when remainder repeats."
def fraction_to_decimal_1(numerator, denominator):
    if numerator == 0:
        return "0"

    # Handle sign
    sign = "-" if (numerator < 0) ^ (denominator < 0) else ""
    n, d = abs(numerator), abs(denominator)

    # Integer part
    result = [sign + str(n // d)]
    remainder = n % d

    if remainder == 0:
        return result[0]

    result.append(".")
    seen = {}  # remainder -> position in result

    while remainder != 0 and remainder not in seen:
        seen[remainder] = len(result)
        remainder *= 10
        result.append(str(remainder // d))
        remainder %= d

    if remainder in seen:
        idx = seen[remainder]
        result.insert(idx, "(")
        result.append(")")

    return "".join(result)


# =============================================================================
# WAY 2: Without Sign Helper (Inline)
# =============================================================================
def fraction_to_decimal_2(numerator, denominator):
    if numerator == 0:
        return "0"

    n, d = abs(numerator), abs(denominator)
    sign = "-" if (numerator < 0) != (denominator < 0) else ""

    result = [sign + str(n // d)]
    remainder = n % d
    if remainder == 0:
        return result[0]

    result.append(".")
    seen = {}

    while remainder and remainder not in seen:
        seen[remainder] = len(result)
        remainder *= 10
        result.append(str(remainder // d))
        remainder %= d

    if remainder in seen:
        idx = seen[remainder]
        result.insert(idx, "(")
        result.append(")")

    return "".join(result)


# =============================================================================
# WAY 3: Using String Concatenation
# =============================================================================
def fraction_to_decimal_3(numerator, denominator):
    if numerator == 0:
        return "0"

    sign = ""
    if (numerator < 0) ^ (denominator < 0):
        sign = "-"

    n, d = abs(numerator), abs(denominator)

    integer_part = n // d
    result = sign + str(integer_part)

    remainder = n % d
    if remainder == 0:
        return result

    result += "."
    seen = {}

    while remainder != 0 and remainder not in seen:
        seen[remainder] = len(result)
        remainder *= 10
        digit = remainder // d
        result += str(digit)
        remainder = remainder % d

    if remainder != 0:
        idx = seen[remainder]
        result = result[:idx] + "(" + result[idx:] + ")"

    return result


# =============================================================================
# WAY 4: Using defaultdict
# =============================================================================
from collections import defaultdict


def fraction_to_decimal_4(numerator, denominator):
    if numerator == 0:
        return "0"

    sign = "-" if (numerator < 0) ^ (denominator < 0) else ""
    n, d = abs(numerator), abs(denominator)

    result = [sign + str(n // d)]
    remainder = n % d
    if remainder == 0:
        return "".join(result)

    result.append(".")
    seen = defaultdict(int)

    while remainder != 0 and not seen[remainder]:
        seen[remainder] = len(result)
        remainder *= 10
        result.append(str(remainder // d))
        remainder %= d

    if seen[remainder]:
        idx = seen[remainder]
        result.insert(idx, "(")
        result.append(")")

    return "".join(result)


# =============================================================================
# WAY 5: One-Pass with Tuple Storage
# =============================================================================
def fraction_to_decimal_5(numerator, denominator):
    if numerator == 0:
        return "0"

    sign = "-" if numerator * denominator < 0 else ""
    n, d = abs(numerator), abs(denominator)

    result = [sign, str(n // d)]
    remainder = n % d

    if remainder:
        result.append(".")
        seen = {}
        while remainder and remainder not in seen:
            seen[remainder] = len(result)
            remainder *= 10
            result.append(str(remainder // d))
            remainder %= d

        if remainder:
            result.insert(seen[remainder], "(")
            result.append(")")

    return "".join(result)


# =============================================================================
# WAY 6: Using divmod for Cleaner Division
# =============================================================================
def fraction_to_decimal_6(numerator, denominator):
    if numerator == 0:
        return "0"

    sign = "-" if (numerator < 0) ^ (denominator < 0) else ""
    n, d = abs(numerator), abs(denominator)

    int_part = n // d
    result = [sign + str(int_part)]
    remainder = n % d

    if remainder == 0:
        return "".join(result)

    result.append(".")
    seen = {}

    while remainder and remainder not in seen:
        seen[remainder] = len(result)
        remainder *= 10
        digit, remainder = divmod(remainder, d)
        result.append(str(digit))

    if remainder in seen:
        idx = seen[remainder]
        result.insert(idx, "(")
        result.append(")")

    return "".join(result)


# =============================================================================
# WAY 7: Using Integer Sign Trick
# =============================================================================
def fraction_to_decimal_7(numerator, denominator):
    if numerator == 0:
        return "0"

    sign = "-" if numerator * denominator < 0 else ""
    n, d = abs(numerator), abs(denominator)

    result = sign + str(n // d)
    remainder = n % d

    if not remainder:
        return result

    result += "."
    seen = {}

    while remainder and remainder not in seen:
        seen[remainder] = len(result)
        remainder *= 10
        result += str(remainder // d)
        remainder %= d

    if remainder:
        result = result[:seen[remainder]] + "(" + result[seen[remainder]:] + ")"

    return result


# =============================================================================
# WAY 8: Recursive Helper Version
# =============================================================================
def fraction_to_decimal_8(numerator, denominator):
    if numerator == 0:
        return "0"

    sign = "-" if (numerator < 0) ^ (denominator < 0) else ""
    n, d = abs(numerator), abs(denominator)

    # Build integer part
    result = [sign + str(n // d)]
    remainder = n % d

    if remainder == 0:
        return "".join(result)

    result.append(".")
    seen = {}

    # Use iteration (recursion would overflow for long repeats)
    i = 0
    while remainder != 0 and remainder not in seen:
        seen[remainder] = i
        remainder *= 10
        result.append(str(remainder // d))
        remainder %= d
        i += 1

    if remainder in seen:
        idx = len(result) - seen[remainder] - 1
        # Find where to insert "(" based on position from end
        insert_pos = len(result) - idx - 1
        result.insert(insert_pos, "(")
        result.append(")")

    return "".join(result)


# =============================================================================
# WAY 9: Functional Style
# =============================================================================
def fraction_to_decimal_9(numerator, denominator):
    if numerator == 0:
        return "0"

    sign = "-" if (numerator < 0) ^ (denominator < 0) else ""
    n, d = abs(numerator), abs(denominator)

    integer = n // d
    remainder = n % d

    if remainder == 0:
        return sign + str(integer)

    result = sign + str(integer) + "."
    seen = {}

    while remainder != 0 and remainder not in seen:
        seen[remainder] = len(result)
        remainder *= 10
        result += str(remainder // d)
        remainder %= d

    if remainder in seen:
        idx = seen[remainder]
        result = result[:idx] + "(" + result[idx:] + ")"

    return result


# =============================================================================
# WAY 10: Most Concise Version
# =============================================================================
def fraction_to_decimal_10(numerator, denominator):
    if not numerator:
        return "0"

    s = "-" if numerator * denominator < 0 else ""
    n, d = abs(numerator), abs(denominator)

    r, seen = n % d, {}
    res = s + str(n // d) + ("." if r else "")

    while r and r not in seen:
        seen[r] = len(res)
        r *= 10
        res += str(r // d)
        r %= d

    if r:
        res = res[:seen[r]] + "(" + res[seen[r]:] + ")"

    return res


# =============================================================================
# HOW I THINK - THE COMPLETE FRAMEWORK
# =============================================================================

HOW_TO_THINK = """
THE THINKING PROCESS FOR THIS PROBLEM:

Step 1: "How does long division work?"
        -> Multiply remainder by 10, divide by denominator
        -> Quotient is next digit, new remainder is what remains
        -> If remainder becomes 0: terminates
        -> If remainder repeats: it cycles forever

Step 2: "When does a decimal repeat?"
        -> When the same remainder appears twice
        -> Because after that, the same digits repeat

Step 3: "How to detect repetition?"
        -> Hashmap: remainder -> position where it first appeared
        -> When we see the same remainder again, insert ( before

Step 4: "What about edge cases?"
        -> numerator = 0 -> return "0"
        -> negative numbers -> handle sign
        -> denominator divides evenly -> no decimal part

Step 5: "How do real implementations work?"
        -> Most languages use this exact approach
        -> Python's fractions module uses GCD for exact fraction
        -> But for decimal string, long division is the way

DECISION TREE:
+----------------+------------------+----------------+
| Concern        | Approach         | Key Insight    |
+----------------+------------------+----------------+
| Sign           | XOR or multiply  | Negative XOR   |
| Integer part   | n // d           | Floor division |
| Decimal part   | Long division    | * 10, // d     |
| Repetition     | Hashmap          | remainder seen |
| Termination    | remainder == 0   | Exact division |
+----------------+------------------+----------------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Basic HashMap", fraction_to_decimal_1),
        ("Way 2: Inline", fraction_to_decimal_2),
        ("Way 3: String concat", fraction_to_decimal_3),
        ("Way 4: defaultdict", fraction_to_decimal_4),
        ("Way 5: Tuple storage", fraction_to_decimal_5),
        ("Way 6: divmod", fraction_to_decimal_6),
        ("Way 7: Sign trick", fraction_to_decimal_7),
        ("Way 8: Recursive", fraction_to_decimal_8),
        ("Way 9: Functional", fraction_to_decimal_9),
        ("Way 10: Concise", fraction_to_decimal_10),
    ]

    test_cases = [
        (1, 2, "0.5"),
        (2, 1, "2"),
        (2, 3, "0.(6)"),
        (1, 6, "0.1(6)"),
        (-1, 2, "-0.5"),
        (-50, 8, "-6.25"),
        (1, 333, "0.(003)"),
        (0, 5, "0"),
        (4, 2, "2"),
        (1, 7, "0.(142857)"),
    ]

    print("=" * 70)
    print("FRACTION TO RECURRING DECIMAL - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        print(f"\n{name}:")
        all_test_pass = True
        for n, d, expected in test_cases:
            try:
                result = func(n, d)
                status = "✓" if result == expected else "✗"
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                print(f"  {status} {n}/{d} = {result} (expected {expected})")
            except Exception as e:
                print(f"  ✗ {n}/{d} = ERROR: {e}")
                all_test_pass = False
                all_pass = False
        print(f"  Overall: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing - see details above")
    print("=" * 70)
    print(HOW_TO_THINK)
