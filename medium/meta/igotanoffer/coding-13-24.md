# Meta DE Coding — 10 Approaches Per Problem (Batch 2: Problems 13-24)

---

## Problem 13 — What is a loop that goes on forever?

This is a knowledge question. The answer is an **infinite loop**. Below are 10 example forms.

### Approach 1 — while True
```python
while True:
    pass
```

### Approach 2 — while with always-true condition
```python
x = 1
while x == 1:
    pass
```

### Approach 3 — for over infinite generator
```python
from itertools import count
for i in count():
    pass
```

### Approach 4 — recursive function without base case
```python
def f(): return f()
f()
```

### Approach 5 — for with range that doesn't end
```python
for i in range(10**18):
    pass
```

### Approach 6 — while not False
```python
while not False:
    pass
```

### Approach 7 — do-while (Python doesn't have one natively, but:)
```python
while True:
    if condition: break
```

### Approach 8 — generator never returns
```python
def gen():
    while True:
        yield 1
for x in gen(): pass
```

### Approach 9 — for over empty iterator? (not actually infinite)
```python
# Counter-example: this terminates
for x in iter([]): pass
```

### Approach 10 — async with never-resolving await
```python
import asyncio
async def f():
    await asyncio.sleep(float('inf'))
asyncio.run(f())
```

**Best answer:** `while True:` is the canonical form. Recursion without base case + generator that never `StopIteration`s are other common patterns.

---

## Problem 14 — Recursively parse a string for a pattern that's 1 or 2 chars

**Pattern:** Tokens of length 1 OR 2 — try every possible split.

### Approach 1 — recursive backtracking with index
```python
def parse(s, i=0):
    if i == len(s): return [[]]
    result = []
    for L in (1, 2):
        if i + L <= len(s):
            for tail in parse(s, i + L):
                result.append([s[i:i+L]] + tail)
    return result
```

### Approach 2 — memoized recursion
```python
from functools import lru_cache
def parse(s):
    @lru_cache(None)
    def go(i):
        if i == len(s): return [[]]
        result = []
        for L in (1, 2):
            if i + L <= len(s):
                for tail in go(i + L):
                    result.append([s[i:i+L]] + tail)
        return result
    return go(0)
```

### Approach 3 — iterative DP
```python
def parse(s):
    n = len(s)
    dp = [[] for _ in range(n+1)]
    dp[n] = [[]]
    for i in range(n-1, -1, -1):
        for L in (1, 2):
            if i+L <= n:
                for tail in dp[i+L]:
                    dp[i].append([s[i:i+L]] + tail)
    return dp[0]
```

### Approach 4 — generator recursion
```python
def parse(s):
    def go(i):
        if i == len(s):
            yield []
            return
        for L in (1, 2):
            if i+L <= len(s):
                for tail in go(i+L):
                    yield [s[i:i+L]] + tail
    return list(go(0))
```

### Approach 5 — BFS with queue
```python
from collections import deque
def parse(s):
    out, q = [], deque([(0, [])])
    while q:
        i, path = q.popleft()
        if i == len(s): out.append(path); continue
        for L in (1, 2):
            if i+L <= len(s):
                q.append((i+L, path + [s[i:i+L]]))
    return out
```

### Approach 6 — iterative stack
```python
def parse(s):
    out, stack = [], [(0, [])]
    while stack:
        i, path = stack.pop()
        if i == len(s): out.append(path); continue
        for L in (2, 1):    # reverse so 1-char processed first
            if i+L <= len(s):
                stack.append((i+L, path + [s[i:i+L]]))
    return out
```

### Approach 7 — reduce
```python
def parse(s):
    def step(states, _):
        new = []
        for i, path in states:
            for L in (1, 2):
                if i+L <= len(s):
                    new.append((i+L, path + [s[i:i+L]]))
        return new
    return [path for _, path in reduce(step, range(len(s)), [(0, [])]) if _ == len(s)]
```

### Approach 8 — closure with state
```python
def parse(s):
    n = len(s)
    def go(i, path):
        if i == n: yield path; return
        for L in (1, 2):
            if i+L <= n:
                yield from go(i+L, path + [s[i:i+L]])
    return list(go(0, []))
```

### Approach 9 — tail-recursion style (Python doesn't optimize but works)
```python
def parse(s):
    def go(i):
        if i == len(s): return [[]]
        out = []
        for L in (1, 2):
            if i+L <= len(s):
                out += [[s[i:i+L]] + t for t in go(i+L)]
        return out
    return go(0)
```

### Approach 10 — DFS with explicit stack + visited
```python
def parse(s):
    out, stack = [], [(0, [])]
    while stack:
        i, path = stack.pop()
        if i == len(s):
            out.append(path)
            continue
        for L in (1, 2):
            if i+L <= len(s):
                stack.append((i+L, path + [s[i:i+L]]))
    return out
```

**Best:** generator version (Approach 4/8) — cleanest and avoids building huge intermediate lists.

---

## Problem 15 — Simple spell-checker

Given a dictionary of valid words, return misspelled words from a document.

### Approach 1 — set difference
```python
def spell_check(doc, dictionary):
    doc_words = doc.split()
    valid = set(dictionary)
    return [w for w in doc_words if w not in valid]
```

### Approach 2 — set with punctuation strip
```python
import string
def spell_check(doc, dictionary):
    valid = set(dictionary)
    return [w for w in doc.translate(str.maketrans('', '', string.punctuation)).split()
            if w not in valid]
```

### Approach 3 — Counter
```python
from collections import Counter
def spell_check(doc, dictionary):
    valid = set(dictionary)
    return [w for w, c in Counter(doc.split()).items() if w not in valid]
```

### Approach 4 — regex tokenize
```python
import re
def spell_check(doc, dictionary):
    valid = set(dictionary)
    return [w for w in re.findall(r"[A-Za-z']+", doc) if w not in valid]
```

### Approach 5 — Trie
```python
class Trie:
    def __init__(self):
        self.children = {}
        self.is_word = False
    def insert(self, w):
        node = self
        for c in w:
            node = node.children.setdefault(c, Trie())
        node.is_word = True
    def contains(self, w):
        node = self
        for c in w:
            if c not in node.children: return False
            node = node.children[c]
        return node.is_word

def spell_check(doc, dictionary):
    t = Trie()
    for w in dictionary: t.insert(w)
    return [w for w in doc.split() if not t.contains(w)]
```

### Approach 6 — fuzzy match via edit distance
```python
def edit_distance(a, b):
    if not a: return len(b)
    if not b: return len(a)
    return min(edit_distance(a[:-1], b) + 1,
               edit_distance(a, b[:-1]) + 1,
               edit_distance(a[:-1], b[:-1]) + (a[-1] != b[-1]))

def spell_check(doc, dictionary, threshold=2):
    return [w for w in doc.split() if min((edit_distance(w, d) for d in dictionary), default=999) > threshold]
```

### Approach 7 — bloom filter style (probabilistic)
```python
# Not exact — for very large dictionaries, use pybloom
# Simplified: use set with hash bucketing
def spell_check(doc, dictionary):
    valid = set(dictionary)
    return [w for w in doc.split() if w not in valid]
```

### Approach 8 — pandas
```python
import pandas as pd
def spell_check(doc, dictionary):
    s = pd.Series(doc.split())
    valid = pd.Series(list(dictionary))
    return s[~s.isin(valid)].tolist()
```

### Approach 9 — dict.get on hash
```python
def spell_check(doc, dictionary):
    valid = {w: True for w in dictionary}
    return [w for w in doc.split() if not valid.get(w)]
```

### Approach 10 — generator with hash lookup
```python
def spell_check(doc, dictionary):
    valid = set(dictionary)
    yield from (w for w in doc.split() if w not in valid)
```

**Best:** set for small dictionary; Trie for very large dictionaries; fuzzy via edit distance if you want suggestions.

---

## Problem 16 — Find the second-highest salary from employee table

### Approach 1 — SQL: LIMIT + OFFSET with DISTINCT
```sql
SELECT DISTINCT salary
FROM employee
ORDER BY salary DESC
LIMIT 1 OFFSET 1;
```

### Approach 2 — SQL: subquery with MAX
```sql
SELECT MAX(salary) AS second_highest
FROM employee
WHERE salary < (SELECT MAX(salary) FROM employee);
```

### Approach 3 — SQL: DENSE_RANK window function
```sql
SELECT salary
FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
      FROM employee) ranked
WHERE rk = 2;
```

### Approach 4 — SQL: window + filter
```sql
WITH ranked AS (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk FROM employee
)
SELECT salary FROM ranked WHERE rk = 2;
```

### Approach 5 — SQL: subquery not equal to max
```sql
SELECT MAX(salary) FROM employee
WHERE salary NOT IN (SELECT MAX(salary) FROM employee);
```

### Approach 6 — Python: pandas
```python
import pandas as pd
def second_highest(df):
    return df['salary'].drop_duplicates().nlargest(2).iloc[-1]
```

### Approach 7 — Python: sort unique
```python
def second_highest(salaries):
    unique = sorted(set(salaries), reverse=True)
    return unique[1] if len(unique) >= 2 else None
```

### Approach 8 — Python: heapq.nlargest
```python
import heapq
def second_highest(salaries):
    return heapq.nlargest(2, set(salaries))[1]
```

### Approach 9 — Python: numpy partition
```python
import numpy as np
def second_highest(salaries):
    arr = np.array(list(set(salaries)))
    return np.partition(arr, -2)[-2]
```

### Approach 10 — SQL: using `WHERE salary <` with correlated subquery
```sql
SELECT e1.salary FROM employee e1
WHERE 1 = (SELECT COUNT(DISTINCT e2.salary) FROM employee e2 WHERE e2.salary > e1.salary);
```

**Best SQL:** window function with `DENSE_RANK` — handles ties.

---

## Problem 17 — Average book price from list

### Approach 1 — sum / len
```python
def avg(prices): return sum(prices) / len(prices)
```

### Approach 2 — statistics.mean
```python
import statistics
def avg(prices): return statistics.mean(prices)
```

### Approach 3 — numpy
```python
import numpy as np
def avg(prices): return float(np.mean(prices))
```

### Approach 4 — pandas
```python
import pandas as pd
def avg(prices): return pd.Series(prices).mean()
```

### Approach 5 — functools.reduce
```python
from functools import reduce
def avg(prices): return reduce(lambda a, b: a+b, prices) / len(prices)
```

### Approach 6 — SQL
```sql
SELECT AVG(price) FROM books;
```

### Approach 7 — generator sum
```python
def avg(prices): return sum(p for p in prices) / sum(1 for _ in prices)
```

### Approach 8 — list comprehension + len
```python
def avg(prices): return sum([p for p in prices]) / len(prices)
```

### Approach 9 — itertools.accumulate
```python
from itertools import accumulate
def avg(prices):
    return list(accumulate(prices))[-1] / len(prices)
```

### Approach 10 — one-pass running mean
```python
def avg(prices):
    total, count = 0, 0
    for p in prices:
        total += p; count += 1
    return total / count
```

**Best:** `sum(prices) / len(prices)`.

---

## Problem 18 — Max unique books within budget (each book bought at most once)

Given book prices and a budget B, maximize the number of distinct books purchased (each at most once). Greedy: buy cheapest first.

### Approach 1 — sort + greedy
```python
def max_books(prices, budget):
    prices = sorted(prices)
    count, spent = 0, 0
    for p in prices:
        if spent + p > budget: break
        spent += p; count += 1
    return count
```

### Approach 2 — heapq + greedy
```python
import heapq
def max_books(prices, budget):
    heapq.heapify(prices)
    count, spent = 0, 0
    while prices:
        p = heapq.heappop(prices)
        if spent + p > budget: break
        spent += p; count += 1
    return count
```

### Approach 3 — accumulate + bisect
```python
from itertools import accumulate
from bisect import bisect_right
def max_books(prices, budget):
    p = sorted(prices)
    cum = list(accumulate(p))
    return bisect_right(cum, budget)
```

### Approach 4 — DP (knapsack for completeness)
```python
def max_books(prices, budget):
    n = len(prices)
    dp = [0] * (budget + 1)
    for p in prices:
        for b in range(budget, p - 1, -1):
            dp[b] = max(dp[b], dp[b-p] + 1)
    return dp[budget]
```

### Approach 5 — DP bitmask (small n only)
```python
def max_books(prices, budget):
    from itertools import combinations
    n = len(prices)
    best = 0
    for r in range(n, 0, -1):
        for combo in combinations(range(n), r):
            if sum(prices[i] for i in combo) <= budget:
                return r
    return 0
```

### Approach 6 — numpy sort + cumsum
```python
import numpy as np
def max_books(prices, budget):
    arr = np.sort(np.array(prices))
    cum = np.cumsum(arr)
    return int((cum <= budget).sum())
```

### Approach 7 — pandas
```python
import pandas as pd
def max_books(prices, budget):
    s = pd.Series(prices).sort_values().cumsum()
    return int((s <= budget).sum())
```

### Approach 8 — sorted enumerate + bisect
```python
from bisect import bisect_right
def max_books(prices, budget):
    p = sorted(prices)
    cum = []
    total = 0
    for x in p:
        total += x; cum.append(total)
    return bisect_right(cum, budget)
```

### Approach 9 — recursive greedy
```python
def max_books(prices, budget):
    prices = sorted(prices)
    def go(i, remaining):
        if i == len(prices) or prices[i] > remaining: return 0
        return 1 + go(i+1, remaining - prices[i])
    return go(0, budget)
```

### Approach 10 — counter-based bucketing
```python
from collections import Counter
def max_books(prices, budget):
    c = Counter(prices)
    spent, count = 0, 0
    for price in sorted(c.keys()):
        take = min(c[price], (budget - spent) // price)
        if take == 0: break
        spent += take * price; count += take
    return count
```

**Best:** sort + greedy for "each at most once" (Approach 1). DP is overkill.

---

## Problem 19 — Identify sequels in title list

**Input:** `['GOT', 'Troy', 'Batman', 'Batman Returns']`
**Output:** `['Batman Returns']`

A sequel = title X is a sequel if X starts with another title Y + " " (followed by something).

### Approach 1 — O(n²) substring scan
```python
def sequels(titles):
    s = set(titles)
    out = []
    for t in titles:
        for other in s:
            if t != other and t.startswith(other + ' '):
                out.append(t); break
    return out
```

### Approach 2 — sort + groupby prefix
```python
from itertools import groupby
def sequels(titles):
    s = sorted(set(titles))
    out = []
    for t in titles:
        for other in s:
            if t.startswith(other + ' '):
                out.append(t); break
    return out
```

### Approach 3 — dict of prefixes
```python
def sequels(titles):
    s = set(titles)
    return [t for t in titles if any(t.startswith(o + ' ') for o in s if o != t)]
```

### Approach 4 — trie-based
```python
class Trie:
    def __init__(self): self.children, self.end = {}, False
    def insert(self, w, original):
        node = self
        for c in w:
            node = node.children.setdefault(c, Trie())
        node.end = original

def sequels(titles):
    t = Trie()
    for x in titles: t.insert(x + ' ', x)
    out = []
    for x in titles:
        node = t
        is_seq = False
        for c in x:
            if c not in node.children: break
            node = node.children[c]
            if node.end and node.end != x:
                is_seq = True; break
        if is_seq: out.append(x)
    return out
```

### Approach 5 — pandas
```python
import pandas as pd
def sequels(titles):
    s = pd.Series(titles)
    base = set(titles)
    mask = s.apply(lambda t: any(t.startswith(o + ' ') for o in base if o != t))
    return s[mask].tolist()
```

### Approach 6 — list comp with split
```python
def sequels(titles):
    s = set(titles)
    def is_seq(t):
        first_word = t.split(' ', 1)[0]
        return first_word in s and first_word != t
    return [t for t in titles if is_seq(t)]
```

### Approach 7 — dict of {first_word: title}
```python
def sequels(titles):
    first_words = {t.split(' ', 1)[0] for t in titles if ' ' in t}
    return [t for t in titles if t.split(' ', 1)[0] in first_words and t not in first_words]
```

### Approach 8 — sorted + adjacent comparison
```python
def sequels(titles):
    s = sorted(set(titles))
    out = []
    for i, t in enumerate(s):
        for j, other in enumerate(s):
            if i != j and t.startswith(other + ' '):
                out.append(t); break
    return out
```

### Approach 9 — regex match
```python
import re
def sequels(titles):
    s = set(titles)
    return [t for t in titles if re.match(r'^(\S+) \S+$', t) and re.match(r'^(\S+) \S+$', t).group(1) in s]
```

### Approach 10 — functools reduce
```python
from functools import reduce
def sequels(titles):
    s = set(titles)
    def keep(acc, t):
        first = t.split(' ', 1)[0]
        return acc + [t] if first in s and first != t else acc
    return reduce(keep, titles, [])
```

**Best:** Approach 7 (first-word lookup) — single pass.

---

## Problem 20 — Most frequent review across books (dict of book → list of reviews)

**Input:** `{'a': ['bal', 'bla'], 'b': ['bla', 'tla', 'dla'], 'c': ['bla', 'tra', 'ura']}`
**Output:** `'bla'`

### Approach 1 — Counter over flattened
```python
from collections import Counter
from itertools import chain
def most_freq(books):
    return Counter(chain.from_iterable(books.values())).most_common(1)[0][0]
```

### Approach 2 — defaultdict + max
```python
from collections import defaultdict
def most_freq(books):
    freq = defaultdict(int)
    for reviews in books.values():
        for r in reviews: freq[r] += 1
    return max(freq, key=freq.get)
```

### Approach 3 — pandas explode
```python
import pandas as pd
def most_freq(books):
    s = pd.DataFrame([{'book': b, 'review': r} for b, rs in books.items() for r in rs])
    return s['review'].value_counts().idxmax()
```

### Approach 4 — reduce
```python
from functools import reduce
from collections import Counter
def most_freq(books):
    flat = reduce(lambda a, b: a + b, books.values(), [])
    return Counter(flat).most_common(1)[0][0]
```

### Approach 5 — sum + Counter
```python
from collections import Counter
def most_freq(books):
    return Counter(sum(books.values(), [])).most_common(1)[0][0]
```

### Approach 6 — manual dict
```python
def most_freq(books):
    freq = {}
    for reviews in books.values():
        for r in reviews:
            freq[r] = freq.get(r, 0) + 1
    return max(freq, key=freq.get)
```

### Approach 7 — numpy
```python
import numpy as np
from collections import Counter
def most_freq(books):
    flat = np.array(sum(books.values(), []))
    return Counter(flat.tolist()).most_common(1)[0][0]
```

### Approach 8 — generator chain
```python
from collections import Counter
from itertools import chain
def most_freq(books):
    return Counter(r for reviews in books.values() for r in reviews).most_common(1)[0][0]
```

### Approach 9 — dict comp with max
```python
def most_freq(books):
    flat = [r for rs in books.values() for r in rs]
    return max(set(flat), key=flat.count)
```

### Approach 10 — Spark-style map-reduce (creative)
```python
from collections import defaultdict
def most_freq(books):
    # Stage 1: map
    mapped = [(r, 1) for rs in books.values() for r in rs]
    # Stage 2: reduce by key
    freq = defaultdict(int)
    for r, c in mapped: freq[r] += c
    return max(freq, key=freq.get)
```

**Best:** Counter on chain.from_iterable.

---

## Problem 21 — Most frequent review across locations, dedup within location

**Input:** `{loc: [reviews...]}`. Dedup reviews within each location, then find most frequent globally.

### Approach 1 — Counter on (set per loc → flatten)
```python
from collections import Counter
from itertools import chain
def most_freq(locations):
    return Counter(chain.from_iterable(set(rs) for rs in locations.values())).most_common(1)[0][0]
```

### Approach 2 — set per location + Counter
```python
from collections import Counter
def most_freq(locations):
    flat = []
    for rs in locations.values():
        flat.extend(set(rs))
    return Counter(flat).most_common(1)[0][0]
```

### Approach 3 — pandas dedup + value_counts
```python
import pandas as pd
def most_freq(locations):
    s = pd.DataFrame([{'loc': l, 'review': r}
                       for l, rs in locations.items() for r in rs]).drop_duplicates()
    return s['review'].value_counts().idxmax()
```

### Approach 4 — defaultdict + dedup
```python
from collections import defaultdict, Counter
def most_freq(locations):
    freq = defaultdict(int)
    for rs in locations.values():
        for r in set(rs): freq[r] += 1
    return max(freq, key=freq.get)
```

### Approach 5 — set chain + Counter
```python
from collections import Counter
def most_freq(locations):
    return Counter(r for rs in locations.values() for r in set(rs)).most_common(1)[0][0]
```

### Approach 6 — manual dict + set
```python
def most_freq(locations):
    freq = {}
    for rs in locations.values():
        for r in set(rs):
            freq[r] = freq.get(r, 0) + 1
    return max(freq, key=freq.get)
```

### Approach 7 — sum of sets + Counter
```python
from collections import Counter
def most_freq(locations):
    return Counter(sum((set(rs) for rs in locations.values()), [])).most_common(1)[0][0]
```

### Approach 8 — functools reduce
```python
from functools import reduce
from collections import Counter
def most_freq(locations):
    flat = reduce(lambda a, b: a + list(set(b)), locations.values(), [])
    return Counter(flat).most_common(1)[0][0]
```

### Approach 9 — map + chain
```python
from collections import Counter
from itertools import chain
def most_freq(locations):
    return Counter(chain(*map(set, locations.values()))).most_common(1)[0][0]
```

### Approach 10 — numpy unique + counts
```python
import numpy as np
def most_freq(locations):
    flat = np.array([r for rs in locations.values() for r in set(rs)])
    vals, counts = np.unique(flat, return_counts=True)
    return str(vals[counts.argmax()])
```

**Best:** Approach 1 (Counter on chained sets).

---

## Problem 22 — Largest odd number from digits of N

**Input:** N (int). Output: largest odd number formed by rearranging digits. If no odd permutation exists, return the original number's largest odd prefix or the largest possible rearrangement.

### Approach 1 — sort digits desc + last odd at end
```python
def largest_odd(n):
    digits = sorted(str(n), reverse=True)
    if int(digits[-1]) % 2 == 1:
        return int(''.join(digits))
    # swap last even with rightmost odd
    for i in range(len(digits)-1, -1, -1):
        if int(digits[i]) % 2 == 1:
            digits.append(digits.pop(i))
            return int(''.join(digits))
    return int(''.join(digits))  # no odd
```

### Approach 2 — count digits, place largest odd last
```python
def largest_odd(n):
    s = str(n)
    odds = sorted([c for c in s if int(c) % 2 == 1], reverse=True)
    evens = sorted([c for c in s if int(c) % 2 == 0], reverse=True)
    if not odds: return int(s)
    return int(''.join(evens + [odds[0]]))
```

### Approach 3 — pandas Series sort
```python
import pandas as pd
def largest_odd(n):
    s = pd.Series(list(str(n))).sort_values(ascending=False).tolist()
    if int(s[-1]) % 2 == 1: return int(''.join(s))
    for i in range(len(s)-1, -1, -1):
        if int(s[i]) % 2 == 1:
            s.append(s.pop(i))
            return int(''.join(s))
    return int(''.join(s))
```

### Approach 4 — heap sort
```python
import heapq
def largest_odd(n):
    digits = []
    for c in str(n):
        heapq.heappush(digits, -int(c))
    sorted_desc = [-heapq.heappop(digits) for _ in range(len(digits))]
    if sorted_desc[-1] % 2 == 1:
        return int(''.join(map(str, sorted_desc)))
    for i in range(len(sorted_desc)-1, -1, -1):
        if sorted_desc[i] % 2 == 1:
            sorted_desc.append(sorted_desc.pop(i))
            return int(''.join(map(str, sorted_desc)))
    return int(''.join(map(str, sorted_desc)))
```

### Approach 5 — Counter + ordering
```python
from collections import Counter
def largest_odd(n):
    c = Counter(str(n))
    odd_chars = sorted([d for d in c if int(d) % 2 == 1], reverse=True)
    even_chars = sorted([d for d in c if int(d) % 2 == 0], reverse=True)
    if not odd_chars: return n
    last = odd_chars[0]
    c[last] -= 1
    if c[last] == 0: del c[last]
    out = []
    for d in even_chars + [d for d in odd_chars if d != last or c[d] > 0]:
        out.append(d * c.get(d, 0))
    return int(''.join(out + [last]))
```

### Approach 6 — string manipulation
```python
def largest_odd(n):
    s = str(n)
    odds = [c for c in s if int(c) % 2 == 1]
    if not odds: return int(s)
    last_odd = max(odds)
    remaining = [c for c in s if c != last_odd or c not in odds]
    odds_remaining = [c for c in odds if c != last_odd]
    evens = [c for c in s if int(c) % 2 == 0]
    return int(''.join(sorted(evens + odds_remaining, reverse=True) + [last_odd]))
```

### Approach 7 — numpy lexsort
```python
import numpy as np
def largest_odd(n):
    digits = np.array(list(str(n)))
    sorted_idx = np.argsort(-digits.astype(int))
    sorted_digits = digits[sorted_idx]
    if int(sorted_digits[-1]) % 2 == 1:
        return int(''.join(sorted_digits))
    for i in range(len(sorted_digits)-1, -1, -1):
        if int(sorted_digits[i]) % 2 == 1:
            odd = sorted_digits[i]
            sorted_digits = np.concatenate([sorted_digits[:i], sorted_digits[i+1:], [odd]])
            return int(''.join(sorted_digits))
    return int(''.join(sorted_digits))
```

### Approach 8 — bucket sort (radix)
```python
def largest_odd(n):
    s = str(n)
    buckets = [[] for _ in range(10)]
    for c in s: buckets[int(c)].append(c)
    out = ''
    for d in range(9, -1, -1):
        out += ''.join(buckets[d])
    if int(out[-1]) % 2 == 1: return int(out)
    for i in range(len(out)-1, -1, -1):
        if int(out[i]) % 2 == 1:
            return int(out[:i] + out[i+1:] + out[i])
    return int(out)
```

### Approach 9 — itertools groupby
```python
from itertools import groupby
def largest_odd(n):
    s = sorted(str(n), reverse=True)
    if int(s[-1]) % 2 == 1: return int(''.join(s))
    evens = [c for c in s if int(c) % 2 == 0]
    odds = [c for c in s if int(c) % 2 == 1]
    if not odds: return int(''.join(s))
    last = odds[0]
    odds = odds[1:]
    return int(''.join(sorted(evens + odds, reverse=True) + [last]))
```

### Approach 10 — recursive
```python
def largest_odd(n):
    s = str(n)
    if not s: return 0
    sorted_s = sorted(s, reverse=True)
    if int(sorted_s[-1]) % 2 == 1:
        return int(''.join(sorted_s))
    odd_positions = [i for i, c in enumerate(sorted_s) if int(c) % 2 == 1]
    if not odd_positions: return int(''.join(sorted_s))
    i = odd_positions[-1]
    odd = sorted_s[i]
    rest = sorted_s[:i] + sorted_s[i+1:]
    return int(''.join(rest + [odd]))
```

**Best:** Approach 2 — sort odds/evens separately, put largest odd last. O(n log n).

---

## Problem 23 — Max total workshops across any two consecutive years (each ≥1)

**Input:** `[(year, count), ...]`. Output: max of `year[i].count + year[i+1].count` for adjacent years.

### Approach 1 — sort + adjacent sum
```python
def max_consecutive(workshops):
    s = sorted(workshops)
    return max(s[i][1] + s[i+1][1] for i in range(len(s)-1))
```

### Approach 2 — groupby year
```python
from itertools import groupby
from collections import defaultdict
def max_consecutive(workshops):
    by_year = defaultdict(int)
    for y, c in workshops: by_year[y] += c
    years = sorted(by_year)
    return max(by_year[y] + by_year[years[i+1]] for i, y in enumerate(years[:-1]))
```

### Approach 3 — pandas
```python
import pandas as pd
def max_consecutive(workshops):
    s = pd.DataFrame(workshops, columns=['year','count']).groupby('year')['count'].sum().sort_index()
    return int((s + s.shift(-1)).max())
```

### Approach 4 — numpy
```python
import numpy as np
def max_consecutive(workshops):
    by_year = {}
    for y, c in workshops: by_year[y] = by_year.get(y, 0) + c
    years = sorted(by_year)
    counts = np.array([by_year[y] for y in years])
    return int((counts[:-1] + counts[1:]).max())
```

### Approach 5 — dict + list comprehension
```python
def max_consecutive(workshops):
    by_year = {}
    for y, c in workshops: by_year[y] = by_year.get(y, 0) + c
    years = sorted(by_year)
    return max(by_year[years[i]] + by_year[years[i+1]] for i in range(len(years)-1))
```

### Approach 6 — sliding window
```python
def max_consecutive(workshops):
    by_year = {}
    for y, c in workshops: by_year[y] = by_year.get(y, 0) + c
    counts = [by_year[y] for y in sorted(by_year)]
    return max(counts[i] + counts[i+1] for i in range(len(counts)-1))
```

### Approach 7 — reduce
```python
from functools import reduce
def max_consecutive(workshops):
    by_year = reduce(lambda d, t: {**d, t[0]: d.get(t[0], 0) + t[1]}, workshops, {})
    counts = [by_year[y] for y in sorted(by_year)]
    return max(counts[i] + counts[i+1] for i in range(len(counts)-1))
```

### Approach 8 — Counter + sorted
```python
from collections import Counter
def max_consecutive(workshops):
    c = Counter()
    for y, n in workshops: c[y] += n
    counts = [c[y] for y in sorted(c)]
    return max(counts[i] + counts[i+1] for i in range(len(counts)-1))
```

### Approach 9 — generator
```python
def max_consecutive(workshops):
    by_year = {}
    for y, n in workshops: by_year[y] = by_year.get(y, 0) + n
    counts = [by_year[y] for y in sorted(by_year)]
    yield max((counts[i] + counts[i+1] for i in range(len(counts)-1)), default=0)
```

### Approach 10 — dict comprehension
```python
def max_consecutive(workshops):
    by_year = {y: sum(c for yy, c in workshops if yy == y) for y, _ in workshops}
    counts = [by_year[y] for y in sorted(by_year)]
    return max(counts[i] + counts[i+1] for i in range(len(counts)-1))
```

**Best:** Approach 1 or 3 (pandas shift trick).

---

## Problem 24 — Smallest number from digits of N (no leading zeros)

**Input:** N (int, positive or negative). Output: smallest number by rearranging digits, no leading zeros.

### Approach 1 — sort asc, but put smallest non-zero first
```python
def smallest(n):
    s = sorted(str(abs(n)))
    if s[0] != '0':
        return int(''.join(s))
    # find first non-zero
    for i, c in enumerate(s):
        if c != '0':
            s[0], s[i] = s[i], s[0]
            break
    return int(''.join(s))
```

### Approach 2 — count zeros, place one non-zero first
```python
def smallest(n):
    s = str(abs(n))
    zeros = s.count('0')
    nonzeros = sorted(c for c in s if c != '0')
    if not nonzeros: return 0
    return int(nonzeros[0] + '0'*zeros + ''.join(nonzeros[1:]))
```

### Approach 3 — Counter
```python
from collections import Counter
def smallest(n):
    s = str(abs(n))
    c = Counter(s)
    if c['0'] == len(s): return 0
    first = sorted(c for c in s if c != '0')[0]
    c[first] -= 1
    out = first
    for d in '0123456789':
        out += d * c.get(d, 0)
    return int(out)
```

### Approach 4 — bucket sort
```python
def smallest(n):
    s = str(abs(n))
    buckets = [[] for _ in range(10)]
    for c in s: buckets[int(c)].append(c)
    # find first non-zero bucket
    first_digit = next(d for d in range(1, 10) if buckets[d])
    buckets[first_digit].pop()
    return int(first_digit.__str__() + '0'*len(buckets[0]) +
               ''.join(str(d) * len(buckets[d]) for d in range(1, 10)))
```

### Approach 5 — pandas
```python
import pandas as pd
def smallest(n):
    s = pd.Series(list(str(abs(n))))
    sorted_s = s.sort_values().tolist()
    if sorted_s[0] != '0':
        return int(''.join(sorted_s))
    nz = next(i for i, c in enumerate(sorted_s) if c != '0')
    sorted_s[0], sorted_s[nz] = sorted_s[nz], sorted_s[0]
    return int(''.join(sorted_s))
```

### Approach 6 — sorted + first non-zero
```python
def smallest(n):
    s = sorted(str(abs(n)))
    for i, c in enumerate(s):
        if c != '0':
            s.insert(0, s.pop(i))
            break
    return int(''.join(s))
```

### Approach 7 — heap + manual
```python
import heapq
def smallest(n):
    digits = list(str(abs(n)))
    heapq.heapify(digits)
    sorted_digits = [heapq.heappop(digits) for _ in range(len(digits))]
    if sorted_digits[0] != '0':
        return int(''.join(sorted_digits))
    for i in range(len(sorted_digits)):
        if sorted_digits[i] != '0':
            sorted_digits[0], sorted_digits[i] = sorted_digits[i], sorted_digits[0]
            return int(''.join(sorted_digits))
    return 0
```

### Approach 8 — numpy
```python
import numpy as np
def smallest(n):
    arr = np.array(list(str(abs(n))))
    sorted_arr = np.sort(arr)
    if sorted_arr[0] != '0':
        return int(''.join(sorted_arr))
    nz = np.where(sorted_arr != '0')[0][0]
    sorted_arr[0], sorted_arr[nz] = sorted_arr[nz], sorted_arr[0]
    return int(''.join(sorted_arr))
```

### Approach 9 — string replace
```python
def smallest(n):
    s = str(abs(n))
    if '0' not in s:
        return int(''.join(sorted(s)))
    sorted_s = sorted(s)
    nz = sorted_s.index(next(c for c in sorted_s if c != '0'))
    sorted_s[0], sorted_s[nz] = sorted_s[nz], sorted_s[0]
    return int(''.join(sorted_s))
```

### Approach 10 — reduce
```python
from functools import reduce
def smallest(n):
    s = sorted(str(abs(n)))
    def step(acc, c):
        if not acc and c == '0': return acc + [c]
        if not acc: return [c] + acc
        return acc + [c]
    return int(''.join(reduce(step, s, [])))
```

**Best:** Approach 2 — count zeros + smallest non-zero first. O(n).
