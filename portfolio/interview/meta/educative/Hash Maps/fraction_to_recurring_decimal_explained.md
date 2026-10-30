# Fraction to Recurring Decimal - 10 Ways with How to Think

## The Problem
```
Convert fraction to decimal string.
If the decimal part repeats, enclose in parentheses.

Examples:
    1/2   -> "0.5"
    2/3   -> "0.(6)"
    1/6   -> "0.1(6)"
    -50/8 -> "-6.25"
```

---

## How I Think (The Mental Process)

### Step 1: "How does long division work?"
> "Multiply remainder by 10, divide by denominator. Quotient is next digit, new remainder is what remains. If remainder becomes 0: terminates. If remainder repeats: cycles forever."

### Step 2: "When does a decimal repeat?"
> "When the same remainder appears twice. Because after that, the same digits repeat."

### Step 3: "How to detect repetition?"
> "Hashmap: remainder -> position where it first appeared. When we see the same remainder again, insert ( before that position."

### Step 4: "Edge cases?"
- numerator = 0 -> return "0"
- Negative numbers -> handle sign
- Denominator divides evenly -> no decimal part

### Step 5: "How do real implementations work?"
> "Most languages use this exact approach. The hashmap tracks remainders, and when a remainder repeats, we know the digits repeat."

---

## Walkthrough Example

```
1/6:
  Step 1: 1/6 = 0 remainder 1          -> "0"
  Step 2: 10/6 = 1 remainder 4         -> "0.1"      remainder=4 (first seen)
  Step 3: 40/6 = 6 remainder 4         -> "0.16"     remainder=4 (SEEN BEFORE!)
  → Insert ( at position where 4 was first seen
  Result: "0.1(6)" ✓
```

```
1/333:
  10/333  = 0 r 10  -> "0.0"  r=10 first
  100/333 = 0 r 100 -> "0.00" r=100 first
  1000/333= 3 r 1   -> "0.003" r=1 first
  10/333  = 0 r 10  -> "0.0030" r=10 SEEN!
  → Insert ( at position 2
  Result: "0.(003)" ✓
```

---

## The 10 Ways

### Way 1: Basic HashMap (BEST - Memorize This!)
```python
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
    seen = {}  # remainder -> position

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
```

### Way 2: Without Sign Helper
Same logic, inline sign check.

### Way 3: Using String Concatenation
Same logic, builds string with `+=` instead of list.

### Way 4: Using defaultdict
Uses `defaultdict(int)` instead of regular dict.

### Way 5: One-Pass with Tuple
Uses `numerator * denominator < 0` for sign check.

### Way 6: Using divmod
```python
digit, remainder = divmod(remainder, d)
```
Cleaner than separate `/` and `%`.

### Way 7: Using Integer Sign Trick
Multiplication check for sign.

### Way 8: Recursive Helper
Iterative with counter variable.

### Way 9: Functional Style
Cleanest version of the algorithm.

### Way 10: Most Concise (Best for Interviews!)
```python
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
```

---

## Decision Tree

```
+----------------+------------------+----------------+
| Concern        | Approach         | Key Insight    |
+----------------+------------------+----------------+
| Sign           | XOR or multiply  | Negative XOR   |
| Integer part   | n // d           | Floor division |
| Decimal part   | Long division    | * 10, // d     |
| Repetition     | Hashmap          | remainder seen |
| Termination    | remainder == 0   | Exact division |
+----------------+------------------+----------------+
```

## Complexity

| Metric | Value |
|--------|-------|
| Time | O(n) where n = length of result |
| Space | O(n) for the hashmap |

## Why This Works (The Math)

In long division, there are only `d-1` possible non-zero remainders. So if we keep going, by pigeonhole principle, we MUST see a repeat. When we do, the digits from that point on are the same as last time.

## Best Answer to Memorize

```python
def fractionToDecimal(numerator, denominator):
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
```

**10 lines. Clean. Optimal. Interview-ready!** 🚀

## Test Cases

| Input | Output | Why |
|-------|--------|-----|
| 1/2 | "0.5" | No repeat |
| 2/3 | "0.(6)" | 6 repeats |
| 1/6 | "0.1(6)" | Only 6 repeats |
| -1/2 | "-0.5" | Negative |
| -50/8 | "-6.25" | Negative + exact |
| 1/333 | "0.(003)" | 3-digit repeat |
| 0/5 | "0" | Zero numerator |
| 4/2 | "2" | Exact division |
| 1/7 | "0.(142857)" | 6-digit repeat |
