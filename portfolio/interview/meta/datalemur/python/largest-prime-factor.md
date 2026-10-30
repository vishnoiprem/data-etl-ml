## Problem
**Largest Prime Factor [Medium]** — Given a positive integer `n`, return the **largest prime factor** of `n`.

If `n` is itself prime, return `n`. For `n = 1`, the answer is `1` (or `None` — clarify).

---

## 1. Simple way to think
- A factor is just something that divides `n` with no remainder.
- Prime factors are factors that are prime.
- To find them, trial-divide `n` by small numbers starting from `2`, `3`, `5`, `6±1`, ...
- Each time you find a divisor `p`, divide `n` by `p` as many times as possible and remember the largest `p` you've seen.
- After you're done, whatever remains in `n` (if greater than 1) is itself a prime factor — possibly the largest.
- This is essentially the sieve of Eratosthenes' factorization approach.

## 2. Interview write-up (how to solve it)
I'll walk through candidate divisors starting from 2, divide out each prime factor completely, and track the largest one I find.

```python
def largest_prime_factor(n):
    if n <= 1:
        return n  # edge case: 1 → 1, 0/undefined undefined

    largest = 1
    d = 2
    while d * d <= n:
        while n % d == 0:
            largest = d
            n //= d
        d += 1 if d == 2 else 2  # after 2, only test odd numbers
    # whatever remains is itself a prime factor
    if n > 1:
        largest = n
    return largest
```

Why this works: any composite factor greater than `sqrt(n)` must be paired with a factor smaller than `sqrt(n)`. So once we've divided out all small primes up to `sqrt(n)`, what remains (1 or a prime) is either trivial or the largest prime factor.

## 3. Best optimized solution
A cleaner version using trial division over odd numbers only after handling 2:

```python
def largest_prime_factor(n):
    if n <= 1:
        return n
    largest = 1
    # strip out factor 2
    while n % 2 == 0:
        largest = 2
        n //= 2
    # strip out odd factors
    d = 3
    while d * d <= n:
        while n % d == 0:
            largest = d
            n //= d
        d += 2
    if n > 1:
        largest = n
    return largest
```

Quick test:
```python
assert largest_prime_factor(1) == 1
assert largest_prime_factor(2) == 2
assert largest_prime_factor(13) == 13
assert largest_prime_factor(13195) == 29     # 5*7*13*29
assert largest_prime_factor(2048) == 2       # 2^11
assert largest_prime_factor(600851475143) == 6857  # Project Euler 3
```

### Why it's optimal
- **O(√n)** time in the worst case — we only trial-dividend up to `√n`.
- **O(1)** space — no recursion, no auxiliary arrays.
- Skipping even numbers after handling 2 cuts iterations roughly in half.

### Common mistakes & interviewer tips
Common mistakes: (1) iterating `d` up to `n` instead of `√n` — that turns a fast algorithm into a TLE; (2) forgetting to update `largest` when you find a divisor; (3) forgetting the final `if n > 1` check, which is the case where the largest prime factor is bigger than any divisor you tried. Tip: if the interviewer asks for "fast factorization of huge numbers," pivot to Pollard's rho — but for `n ≤ 10^12` trial division is plenty.