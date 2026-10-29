MOD = 10**9 + 7


def numberOfGoodSubsets(nums):
    """
    Count subsets whose product is a product of two or more distinct
    primes (each prime appears at most once, and the subset is non-trivial:
    product is not a single prime).
    Return the answer modulo 10^9 + 7.

    Key insight: nums[i] <= 30, so only these primes matter:
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29  (10 primes).

    Represent a subset's product by a 10-bit mask of which primes appear.
    A number 2..30 is "valid" if it's square-free AND composite
    (i.e., its prime factorization has at least 2 distinct primes).
    Wait - actually we also need to include primes themselves because they
    can pair with other primes. A prime n contributes its single bit to
    the mask; the product mask is square-free iff no two numbers share a
    prime factor.
    """
    # Count frequency of each value
    cnt = [0] * 31
    for x in nums:
        cnt[x] += 1

    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    p_idx = {p: i for i, p in enumerate(primes)}

    # For each n in 2..30, compute its prime mask (if square-free).
    mask_of = [0] * 31
    valid = [False] * 31

    for n in range(2, 31):
        x = n
        m = 0
        ok = True
        for p in primes:
            while x % p == 0:
                if m & (1 << p_idx[p]):
                    ok = False
                    break
                m |= 1 << p_idx[p]
                x //= p
            if not ok:
                break
        if x != 1:
            ok = False  # has prime factor > 29
        valid[n] = ok
        mask_of[n] = m

    # DP over masks: dp[mask] = number of subsets whose product has exactly
    # the prime set given by `mask` (each occurrence is a distinct element).
    dp = [0] * (1 << 10)
    dp[0] = 1  # empty subset

    for n in range(2, 31):
        if cnt[n] == 0 or not valid[n]:
            continue
        m = mask_of[n]
        ways = cnt[n]
        for old_mask in range(1 << 10):
            if old_mask & m == 0:
                dp[old_mask | m] = (dp[old_mask | m] + dp[old_mask] * ways) % MOD

    # Count good subsets: masks with at least 2 distinct primes set,
    # excluding the empty subset (mask=0).
    good = 0
    for mask in range(1, 1 << 10):
        if mask & (mask - 1) == 0:  # only one bit set => single prime
            continue
        good = (good + dp[mask]) % MOD

    # Each occurrence of `1` can be included or excluded independently.
    # 1 doesn't change the product, so multiply by 2^(count_of_1).
    ones = cnt[1]
    if ones:
        good = good * pow(2, ones, MOD) % MOD

    return good


if __name__ == "__main__":
    # Test cases
    print(numberOfGoodSubsets([1, 2, 5, 6]))    # 6
    print(numberOfGoodSubsets([4, 2, 3, 7]))    # 4
    print(numberOfGoodSubsets([2, 3, 5]))       # 4
