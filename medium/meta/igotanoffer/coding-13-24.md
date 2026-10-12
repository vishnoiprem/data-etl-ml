# Meta DE Coding — 10 Approaches Per Problem (Batch 2: Problems 13-24)

Each problem is solved 10 different ways. Approaches ordered from most idiomatic to most creative.
All code uses explicit `for` loops with full step-by-step logic for clarity.

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
def f():
    return f()
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
    if condition:
        break
```

### Approach 8 — generator never returns
```python
def gen():
    while True:
        yield 1
for x in gen():
    pass
```

### Approach 9 — for over empty iterator? (not actually infinite)
```python
for x in iter([]):
    pass
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

**Input:** `s = "abc"`, split into tokens of length 1 or 2.
**Output:** All possible tokenizations, e.g. `[['a','b','c'], ['a','bc'], ['ab','c'], ['ab','c']]`

### Approach 1 — recursive backtracking with index
```python
def parse(s, i=0):
    if i == len(s):
        return [[]]
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
        if i == len(s):
            return [[]]
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
    out = []
    for x in go(0):
        out.append(x)
    return out
```

### Approach 5 — BFS with queue
```python
from collections import deque
def parse(s):
    out = []
    q = deque([(0, [])])
    while q:
        i, path = q.popleft()
        if i == len(s):
            out.append(path)
            continue
        for L in (1, 2):
            if i+L <= len(s):
                q.append((i+L, path + [s[i:i+L]]))
    return out
```

### Approach 6 — iterative stack
```python
def parse(s):
    out = []
    stack = [(0, [])]
    while stack:
        i, path = stack.pop()
        if i == len(s):
            out.append(path)
            continue
        for L in (2, 1):
            if i+L <= len(s):
                stack.append((i+L, path + [s[i:i+L]]))
    return out
```

### Approach 7 — reduce
```python
from functools import reduce
def parse(s):
    def step(states, _):
        new = []
        for i, path in states:
            for L in (1, 2):
                if i+L <= len(s):
                    new.append((i+L, path + [s[i:i+L]]))
        return new
    final = reduce(step, range(len(s)), [(0, [])])
    out = []
    for i, path in final:
        if i == len(s):
            out.append(path)
    return out
```

### Approach 8 — closure with state
```python
def parse(s):
    n = len(s)
    def go(i, path):
        if i == n:
            yield path
            return
        for L in (1, 2):
            if i+L <= n:
                yield from go(i+L, path + [s[i:i+L]])
    out = []
    for x in go(0, []):
        out.append(x)
    return out
```

### Approach 9 — tail-recursion style (Python doesn't optimize but works)
```python
def parse(s):
    def go(i):
        if i == len(s):
            return [[]]
        out = []
        for L in (1, 2):
            if i+L <= len(s):
                for t in go(i+L):
                    out.append([s[i:i+L]] + t)
        return out
    return go(0)
```

### Approach 10 — DFS with explicit stack + visited
```python
def parse(s):
    out = []
    stack = [(0, [])]
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
    out = []
    for w in doc_words:
        if w not in valid:
            out.append(w)
    return out
```

### Approach 2 — set with punctuation strip
```python
import string
def spell_check(doc, dictionary):
    valid = set(dictionary)
    cleaned = doc.translate(str.maketrans('', '', string.punctuation))
    out = []
    for w in cleaned.split():
        if w not in valid:
            out.append(w)
    return out
```

### Approach 3 — Counter
```python
from collections import Counter
def spell_check(doc, dictionary):
    valid = set(dictionary)
    counts = Counter(doc.split())
    out = []
    for w, c in counts.items():
        if w not in valid:
            out.append(w)
    return out
```

### Approach 4 — regex tokenize
```python
import re
def spell_check(doc, dictionary):
    valid = set(dictionary)
    out = []
    for w in re.findall(r"[A-Za-z']+", doc):
        if w not in valid:
            out.append(w)
    return out
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
            if c not in node.children:
                node.children[c] = Trie()
            node = node.children[c]
        node.is_word = True
    def contains(self, w):
        node = self
        for c in w:
            if c not in node.children:
                return False
            node = node.children[c]
        return node.is_word

def spell_check(doc, dictionary):
    t = Trie()
    for w in dictionary:
        t.insert(w)
    out = []
    for w in doc.split():
        if not t.contains(w):
            out.append(w)
    return out
```

### Approach 6 — fuzzy match via edit distance
```python
def edit_distance(a, b):
    if not a:
        return len(b)
    if not b:
        return len(a)
    sub_cost = 0 if a[-1] == b[-1] else 1
    return min(
        edit_distance(a[:-1], b) + 1,
        edit_distance(a, b[:-1]) + 1,
        edit_distance(a[:-1], b[:-1]) + sub_cost
    )

def spell_check(doc, dictionary, threshold=2):
    out = []
    for w in doc.split():
        best = 999
        for d in dictionary:
            dist = edit_distance(w, d)
            if dist < best:
                best = dist
        if best > threshold:
            out.append(w)
    return out
```

### Approach 7 — bloom filter style (probabilistic)
```python
def spell_check(doc, dictionary):
    valid = set(dictionary)
    out = []
    for w in doc.split():
        if w not in valid:
            out.append(w)
    return out
```

### Approach 8 — pandas
```python
import pandas as pd
def spell_check(doc, dictionary):
    s = pd.Series(doc.split())
    valid = pd.Series(list(dictionary))
    masked = s[~s.isin(valid)]
    out = []
    for v in masked:
        out.append(v)
    return out
```

### Approach 9 — dict.get on hash
```python
def spell_check(doc, dictionary):
    valid = {}
    for w in dictionary:
        valid[w] = True
    out = []
    for w in doc.split():
        if not valid.get(w):
            out.append(w)
    return out
```

### Approach 10 — generator with hash lookup
```python
def spell_check(doc, dictionary):
    valid = set(dictionary)
    def gen():
        for w in doc.split():
            if w not in valid:
                yield w
    out = []
    for w in gen():
        out.append(w)
    return out
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
    s = df['salary'].drop_duplicates()
    sorted_s = s.sort_values(ascending=False)
    n = len(sorted_s)
    if n < 2:
        return None
    return sorted_s.iloc[1]
```

### Approach 7 — Python: sort unique
```python
def second_highest(salaries):
    unique_set = set()
    for s in salaries:
        unique_set.add(s)
    unique = []
    for x in unique_set:
        unique.append(x)
    unique.sort(reverse=True)
    if len(unique) >= 2:
        return unique[1]
    return None
```

### Approach 8 — Python: heapq.nlargest
```python
import heapq
def second_highest(salaries):
    unique_set = set()
    for s in salaries:
        unique_set.add(s)
    top2 = heapq.nlargest(2, unique_set)
    if len(top2) >= 2:
        return top2[1]
    return None
```

### Approach 9 — Python: numpy partition
```python
import numpy as np
def second_highest(salaries):
    unique_set = set()
    for s in salaries:
        unique_set.add(s)
    arr = np.array(list(unique_set))
    if len(arr) < 2:
        return None
    partitioned = np.partition(arr, -2)
    return int(partitioned[-2])
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
def avg(prices):
    total = 0
    for p in prices:
        total += p
    return total / len(prices)
```

### Approach 2 — statistics.mean
```python
import statistics
def avg(prices):
    return statistics.mean(prices)
```

### Approach 3 — numpy
```python
import numpy as np
def avg(prices):
    return float(np.mean(prices))
```

### Approach 4 — pandas
```python
import pandas as pd
def avg(prices):
    return float(pd.Series(prices).mean())
```

### Approach 5 — functools.reduce
```python
from functools import reduce
def avg(prices):
    total = reduce(lambda a, b: a + b, prices, 0)
    return total / len(prices)
```

### Approach 6 — SQL
```sql
SELECT AVG(price) FROM books;
```

### Approach 7 — generator sum
```python
def avg(prices):
    total = 0
    count = 0
    for p in prices:
        total += p
        count += 1
    return total / count
```

### Approach 8 — list comprehension + len
```python
def avg(prices):
    arr = []
    for p in prices:
        arr.append(p)
    return sum(arr) / len(arr)
```

### Approach 9 — itertools.accumulate
```python
from itertools import accumulate
def avg(prices):
    last = None
    for x in accumulate(prices):
        last = x
    if last is None:
        return 0
    return last / len(prices)
```

### Approach 10 — one-pass running mean
```python
def avg(prices):
    total = 0
    count = 0
    for p in prices:
        total += p
        count += 1
    return total / count
```

**Best:** `sum(prices) / len(prices)`.

---

## Problem 18 — Max unique books within budget (each book bought at most once)

Given book prices and a budget B, maximize the number of distinct books purchased (each at most once). Greedy: buy cheapest first.

### Approach 1 — sort + greedy
```python
def max_books(prices, budget):
    prices_sorted = sorted(prices)
    count = 0
    spent = 0
    for p in prices_sorted:
        if spent + p > budget:
            break
        spent += p
        count += 1
    return count
```

### Approach 2 — heapq + greedy
```python
import heapq
def max_books(prices, budget):
    heapq.heapify(prices)
    count = 0
    spent = 0
    while prices:
        p = heapq.heappop(prices)
        if spent + p > budget:
            break
        spent += p
        count += 1
    return count
```

### Approach 3 — accumulate + bisect
```python
from itertools import accumulate
from bisect import bisect_right
def max_books(prices, budget):
    p = sorted(prices)
    cum = []
    last = 0
    for x in accumulate(p):
        last = x
        cum.append(last)
    return bisect_right(cum, budget)
```

### Approach 4 — DP (knapsack for completeness)
```python
def max_books(prices, budget):
    n = len(prices)
    dp = [0] * (budget + 1)
    for p in prices:
        for b in range(budget, p - 1, -1):
            if dp[b-p] + 1 > dp[b]:
                dp[b] = dp[b-p] + 1
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
            total = 0
            for i in combo:
                total += prices[i]
            if total <= budget:
                return r
    return 0
```

### Approach 6 — numpy sort + cumsum
```python
import numpy as np
def max_books(prices, budget):
    arr = np.sort(np.array(prices))
    cum = np.cumsum(arr)
    count = 0
    for v in cum:
        if v <= budget:
            count += 1
        else:
            break
    return int(count)
```

### Approach 7 — pandas
```python
import pandas as pd
def max_books(prices, budget):
    s = pd.Series(prices).sort_values()
    cum = s.cumsum()
    count = 0
    for v in cum:
        if v <= budget:
            count += 1
        else:
            break
    return int(count)
```

### Approach 8 — sorted enumerate + bisect
```python
from bisect import bisect_right
def max_books(prices, budget):
    p = sorted(prices)
    cum = []
    total = 0
    for x in p:
        total += x
        cum.append(total)
    return bisect_right(cum, budget)
```

### Approach 9 — recursive greedy
```python
def max_books(prices, budget):
    prices_sorted = sorted(prices)
    def go(i, remaining):
        if i == len(prices_sorted):
            return 0
        if prices_sorted[i] > remaining:
            return 0
        return 1 + go(i+1, remaining - prices_sorted[i])
    return go(0, budget)
```

### Approach 10 — counter-based bucketing
```python
from collections import Counter
def max_books(prices, budget):
    c = Counter(prices)
    spent = 0
    count = 0
    for price in sorted(c.keys()):
        take = min(c[price], (budget - spent) // price)
        if take == 0:
            break
        spent += take * price
        count += take
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
    s = set()
    for t in titles:
        s.add(t)
    out = []
    for t in titles:
        is_seq = False
        for other in s:
            if t != other and t.startswith(other + ' '):
                is_seq = True
                break
        if is_seq:
            out.append(t)
    return out
```

### Approach 2 — sort + groupby prefix
```python
from itertools import groupby
def sequels(titles):
    s_set = set()
    for t in titles:
        s_set.add(t)
    s = []
    for x in s_set:
        s.append(x)
    s.sort()
    out = []
    for t in titles:
        is_seq = False
        for other in s:
            if t.startswith(other + ' '):
                is_seq = True
                break
        if is_seq:
            out.append(t)
    return out
```

### Approach 3 — dict of prefixes
```python
def sequels(titles):
    s = set()
    for t in titles:
        s.add(t)
    out = []
    for t in titles:
        found = False
        for o in s:
            if o != t and t.startswith(o + ' '):
                found = True
                break
        if found:
            out.append(t)
    return out
```

### Approach 4 — trie-based
```python
class Trie:
    def __init__(self):
        self.children = {}
        self.end = False
        self.original = None
    def insert(self, w, original):
        node = self
        for c in w:
            if c not in node.children:
                node.children[c] = Trie()
            node = node.children[c]
        node.end = True
        node.original = original

def sequels(titles):
    t = Trie()
    for x in titles:
        t.insert(x + ' ', x)
    out = []
    for x in titles:
        node = t
        is_seq = False
        for c in x:
            if c not in node.children:
                break
            node = node.children[c]
            if node.end and node.original != x:
                is_seq = True
                break
        if is_seq:
            out.append(x)
    return out
```

### Approach 5 — pandas
```python
import pandas as pd
def sequels(titles):
    s = pd.Series(titles)
    base = set()
    for t in titles:
        base.add(t)
    mask = []
    for t in titles:
        found = False
        for o in base:
            if o != t and t.startswith(o + ' '):
                found = True
                break
        mask.append(found)
    filtered = s[mask]
    out = []
    for v in filtered:
        out.append(v)
    return out
```

### Approach 6 — list comp with split
```python
def sequels(titles):
    s = set()
    for t in titles:
        s.add(t)
    def is_seq(t):
        first_word = t.split(' ', 1)[0]
        return first_word in s and first_word != t
    out = []
    for t in titles:
        if is_seq(t):
            out.append(t)
    return out
```

### Approach 7 — dict of {first_word: title}
```python
def sequels(titles):
    first_words = set()
    for t in titles:
        if ' ' in t:
            fw = t.split(' ', 1)[0]
            first_words.add(fw)
    out = []
    for t in titles:
        fw = t.split(' ', 1)[0]
        if fw in first_words and t not in first_words:
            out.append(t)
    return out
```

### Approach 8 — sorted + adjacent comparison
```python
def sequels(titles):
    s_set = set()
    for t in titles:
        s_set.add(t)
    s = []
    for x in s_set:
        s.append(x)
    s.sort()
    out = []
    for i in range(len(s)):
        for j in range(len(s)):
            if i != j and s[i].startswith(s[j] + ' '):
                out.append(s[i])
                break
    return out
```

### Approach 9 — regex match
```python
import re
def sequels(titles):
    s = set()
    for t in titles:
        s.add(t)
    out = []
    for t in titles:
        m = re.match(r'^(\S+) \S+$', t)
        if m and m.group(1) in s:
            out.append(t)
    return out
```

### Approach 10 — functools reduce
```python
from functools import reduce
def sequels(titles):
    s = set()
    for t in titles:
        s.add(t)
    def keep(acc, t):
        first = t.split(' ', 1)[0]
        if first in s and first != t:
            acc.append(t)
        return acc
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
    all_reviews = []
    for reviews in books.values():
        for r in reviews:
            all_reviews.append(r)
    c = Counter(all_reviews)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 2 — defaultdict + max
```python
from collections import defaultdict
def most_freq(books):
    freq = defaultdict(int)
    for reviews in books.values():
        for r in reviews:
            freq[r] += 1
    best = None
    best_n = -1
    for k, v in freq.items():
        if v > best_n:
            best_n = v
            best = k
    return best
```

### Approach 3 — pandas explode
```python
import pandas as pd
def most_freq(books):
    rows = []
    for b, rs in books.items():
        for r in rs:
            rows.append({'book': b, 'review': r})
    s = pd.DataFrame(rows)
    counts = s['review'].value_counts()
    return counts.idxmax()
```

### Approach 4 — reduce
```python
from functools import reduce
from collections import Counter
def most_freq(books):
    flat = reduce(lambda a, b: a + b, books.values(), [])
    c = Counter(flat)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 5 — sum + Counter
```python
from collections import Counter
def most_freq(books):
    flat = []
    for rs in books.values():
        for r in rs:
            flat.append(r)
    c = Counter(flat)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 6 — manual dict
```python
def most_freq(books):
    freq = {}
    for reviews in books.values():
        for r in reviews:
            freq[r] = freq.get(r, 0) + 1
    best = None
    best_n = -1
    for k, v in freq.items():
        if v > best_n:
            best_n = v
            best = k
    return best
```

### Approach 7 — numpy
```python
import numpy as np
from collections import Counter
def most_freq(books):
    flat_list = []
    for rs in books.values():
        for r in rs:
            flat_list.append(r)
    arr = np.array(flat_list)
    c = Counter(arr.tolist())
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 8 — generator chain
```python
from collections import Counter
def most_freq(books):
    all_reviews = []
    for reviews in books.values():
        for r in reviews:
            all_reviews.append(r)
    c = Counter(all_reviews)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 9 — dict comp with max
```python
def most_freq(books):
    flat = []
    for rs in books.values():
        for r in rs:
            flat.append(r)
    uniq = set(flat)
    best = None
    best_n = -1
    for u in uniq:
        count = 0
        for f in flat:
            if f == u:
                count += 1
        if count > best_n:
            best_n = count
            best = u
    return best
```

### Approach 10 — Spark-style map-reduce (creative)
```python
from collections import defaultdict
def most_freq(books):
    mapped = []
    for rs in books.values():
        for r in rs:
            mapped.append((r, 1))
    freq = defaultdict(int)
    for r, c in mapped:
        freq[r] += c
    best = None
    best_n = -1
    for k, v in freq.items():
        if v > best_n:
            best_n = v
            best = k
    return best
```

**Best:** Counter on chain.from_iterable.

---

## Problem 21 — Most frequent review across locations, dedup within location

**Input:** `{loc: [reviews...]}`. Dedup reviews within each location, then find most frequent globally.

### Approach 1 — Counter on (set per loc → flatten)
```python
from collections import Counter
def most_freq(locations):
    deduped = []
    for rs in locations.values():
        uniq = []
        seen = set()
        for r in rs:
            if r not in seen:
                seen.add(r)
                uniq.append(r)
        for u in uniq:
            deduped.append(u)
    c = Counter(deduped)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 2 — set per location + Counter
```python
from collections import Counter
def most_freq(locations):
    flat = []
    for rs in locations.values():
        uniq = set()
        for r in rs:
            uniq.add(r)
        for u in uniq:
            flat.append(u)
    c = Counter(flat)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 3 — pandas dedup + value_counts
```python
import pandas as pd
def most_freq(locations):
    rows = []
    for l, rs in locations.items():
        for r in rs:
            rows.append({'loc': l, 'review': r})
    s = pd.DataFrame(rows).drop_duplicates()
    counts = s['review'].value_counts()
    return counts.idxmax()
```

### Approach 4 — defaultdict + dedup
```python
from collections import defaultdict
def most_freq(locations):
    freq = defaultdict(int)
    for rs in locations.values():
        uniq = set()
        for r in rs:
            uniq.add(r)
        for u in uniq:
            freq[u] += 1
    best = None
    best_n = -1
    for k, v in freq.items():
        if v > best_n:
            best_n = v
            best = k
    return best
```

### Approach 5 — set chain + Counter
```python
from collections import Counter
def most_freq(locations):
    all_reviews = []
    for rs in locations.values():
        uniq = set()
        for r in rs:
            uniq.add(r)
        for u in uniq:
            all_reviews.append(u)
    c = Counter(all_reviews)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 6 — manual dict + set
```python
def most_freq(locations):
    freq = {}
    for rs in locations.values():
        uniq = set()
        for r in rs:
            uniq.add(r)
        for u in uniq:
            freq[u] = freq.get(u, 0) + 1
    best = None
    best_n = -1
    for k, v in freq.items():
        if v > best_n:
            best_n = v
            best = k
    return best
```

### Approach 7 — sum of sets + Counter
```python
from collections import Counter
def most_freq(locations):
    sets = []
    for rs in locations.values():
        u = set()
        for r in rs:
            u.add(r)
        sets.append(u)
    flat = []
    for s in sets:
        for x in s:
            flat.append(x)
    c = Counter(flat)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 8 — functools reduce
```python
from functools import reduce
from collections import Counter
def most_freq(locations):
    flat = reduce(lambda a, b: a + list(set(b)), locations.values(), [])
    c = Counter(flat)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 9 — map + chain
```python
from collections import Counter
def most_freq(locations):
    all_reviews = []
    for rs in locations.values():
        u = set()
        for r in rs:
            u.add(r)
        for x in u:
            all_reviews.append(x)
    c = Counter(all_reviews)
    top = c.most_common(1)
    if not top:
        return None
    return top[0][0]
```

### Approach 10 — numpy unique + counts
```python
import numpy as np
def most_freq(locations):
    flat_list = []
    for rs in locations.values():
        u = set()
        for r in rs:
            u.add(r)
        for x in u:
            flat_list.append(x)
    flat = np.array(flat_list)
    vals, counts = np.unique(flat, return_counts=True)
    best_idx = 0
    best_n = -1
    for i in range(len(counts)):
        if counts[i] > best_n:
            best_n = counts[i]
            best_idx = i
    return str(vals[best_idx])
```

**Best:** Approach 1 (Counter on chained sets).

---

## Problem 22 — Largest odd number from digits of N

**Input:** N (int). Output: largest odd number formed by rearranging digits. If no odd permutation exists, return the original number's largest odd prefix or the largest possible rearrangement.

### Approach 1 — sort digits desc + last odd at end
```python
def largest_odd(n):
    s = str(n)
    digits = []
    for c in s:
        digits.append(c)
    digits.sort(reverse=True)
    if int(digits[-1]) % 2 == 1:
        out = ''
        for d in digits:
            out += d
        return int(out)
    for i in range(len(digits)-1, -1, -1):
        if int(digits[i]) % 2 == 1:
            odd = digits.pop(i)
            digits.append(odd)
            out = ''
            for d in digits:
                out += d
            return int(out)
    out = ''
    for d in digits:
        out += d
    return int(out)
```

### Approach 2 — count digits, place largest odd last
```python
def largest_odd(n):
    s = str(n)
    odds = []
    evens = []
    for c in s:
        if int(c) % 2 == 1:
            odds.append(c)
        else:
            evens.append(c)
    odds.sort(reverse=True)
    evens.sort(reverse=True)
    if not odds:
        return int(s)
    out = ''
    for d in evens:
        out += d
    out += odds[0]
    return int(out)
```

### Approach 3 — pandas Series sort
```python
import pandas as pd
def largest_odd(n):
    s_list = []
    for c in str(n):
        s_list.append(c)
    s = pd.Series(s_list)
    sorted_s_list = []
    for v in s.sort_values(ascending=False):
        sorted_s_list.append(v)
    if int(sorted_s_list[-1]) % 2 == 1:
        out = ''
        for d in sorted_s_list:
            out += d
        return int(out)
    for i in range(len(sorted_s_list)-1, -1, -1):
        if int(sorted_s_list[i]) % 2 == 1:
            odd = sorted_s_list.pop(i)
            sorted_s_list.append(odd)
            out = ''
            for d in sorted_s_list:
                out += d
            return int(out)
    out = ''
    for d in sorted_s_list:
        out += d
    return int(out)
```

### Approach 4 — heap sort
```python
import heapq
def largest_odd(n):
    digits = []
    for c in str(n):
        heapq.heappush(digits, -int(c))
    sorted_desc = []
    while digits:
        sorted_desc.append(-heapq.heappop(digits))
    if sorted_desc[-1] % 2 == 1:
        out = ''
        for d in sorted_desc:
            out += str(d)
        return int(out)
    for i in range(len(sorted_desc)-1, -1, -1):
        if sorted_desc[i] % 2 == 1:
            odd = sorted_desc.pop(i)
            sorted_desc.append(odd)
            out = ''
            for d in sorted_desc:
                out += str(d)
            return int(out)
    out = ''
    for d in sorted_desc:
        out += str(d)
    return int(out)
```

### Approach 5 — Counter + ordering
```python
from collections import Counter
def largest_odd(n):
    s = str(n)
    c = Counter(s)
    odd_chars = []
    even_chars = []
    for d in c:
        if int(d) % 2 == 1:
            odd_chars.append(d)
        else:
            even_chars.append(d)
    odd_chars.sort(reverse=True)
    even_chars.sort(reverse=True)
    if not odd_chars:
        return n
    last = odd_chars[0]
    c[last] -= 1
    if c[last] == 0:
        del c[last]
    out = ''
    for d in even_chars:
        out += d * c.get(d, 0)
    for d in odd_chars:
        if d == last and c.get(d, 0) == 0:
            continue
        out += d * c.get(d, 0)
    out += last
    return int(out)
```

### Approach 6 — string manipulation
```python
def largest_odd(n):
    s = str(n)
    odds = []
    for c in s:
        if int(c) % 2 == 1:
            odds.append(c)
    if not odds:
        return int(s)
    last_odd = max(odds)
    remaining = []
    for c in s:
        if c != last_odd or c not in odds:
            remaining.append(c)
    odds_remaining = []
    for c in odds:
        if c != last_odd:
            odds_remaining.append(c)
    evens = []
    for c in s:
        if int(c) % 2 == 0:
            evens.append(c)
    combined = evens + odds_remaining
    combined.sort(reverse=True)
    out = ''
    for d in combined:
        out += d
    out += last_odd
    return int(out)
```

### Approach 7 — numpy lexsort
```python
import numpy as np
def largest_odd(n):
    s = str(n)
    digits_list = []
    for c in s:
        digits_list.append(c)
    digits = np.array(digits_list)
    int_digits = []
    for d in digits:
        int_digits.append(int(d))
    int_arr = np.array(int_digits)
    sorted_idx = np.argsort(-int_arr)
    sorted_list = []
    for i in sorted_idx:
        sorted_list.append(str(digits[i]))
    if int(sorted_list[-1]) % 2 == 1:
        out = ''
        for d in sorted_list:
            out += d
        return int(out)
    for i in range(len(sorted_list)-1, -1, -1):
        if int(sorted_list[i]) % 2 == 1:
            odd = sorted_list[i]
            new_list = []
            for j in range(len(sorted_list)):
                if j != i:
                    new_list.append(sorted_list[j])
            new_list.append(odd)
            out = ''
            for d in new_list:
                out += d
            return int(out)
    out = ''
    for d in sorted_list:
        out += d
    return int(out)
```

### Approach 8 — bucket sort (radix)
```python
def largest_odd(n):
    s = str(n)
    buckets = []
    for _ in range(10):
        buckets.append([])
    for c in s:
        buckets[int(c)].append(c)
    out = ''
    for d in range(9, -1, -1):
        for c in buckets[d]:
            out += c
    if int(out[-1]) % 2 == 1:
        return int(out)
    for i in range(len(out)-1, -1, -1):
        if int(out[i]) % 2 == 1:
            new_out = out[:i] + out[i+1:] + out[i]
            return int(new_out)
    return int(out)
```

### Approach 9 — itertools groupby
```python
def largest_odd(n):
    s_list = []
    for c in str(n):
        s_list.append(c)
    s_list.sort(reverse=True)
    if int(s_list[-1]) % 2 == 1:
        out = ''
        for d in s_list:
            out += d
        return int(out)
    evens = []
    odds = []
    for c in s_list:
        if int(c) % 2 == 0:
            evens.append(c)
        else:
            odds.append(c)
    if not odds:
        out = ''
        for d in s_list:
            out += d
        return int(out)
    last = odds[0]
    odds = odds[1:]
    combined = evens + odds
    combined.sort(reverse=True)
    out = ''
    for d in combined:
        out += d
    out += last
    return int(out)
```

### Approach 10 — recursive
```python
def largest_odd(n):
    s = str(n)
    if not s:
        return 0
    s_list = []
    for c in s:
        s_list.append(c)
    s_list.sort(reverse=True)
    if int(s_list[-1]) % 2 == 1:
        out = ''
        for d in s_list:
            out += d
        return int(out)
    odd_positions = []
    for i, c in enumerate(s_list):
        if int(c) % 2 == 1:
            odd_positions.append(i)
    if not odd_positions:
        out = ''
        for d in s_list:
            out += d
        return int(out)
    i = odd_positions[-1]
    odd = s_list[i]
    rest = []
    for j in range(len(s_list)):
        if j != i:
            rest.append(s_list[j])
    rest.append(odd)
    out = ''
    for d in rest:
        out += d
    return int(out)
```

**Best:** Approach 2 — sort odds/evens separately, put largest odd last. O(n log n).

---

## Problem 23 — Max total workshops across any two consecutive years (each ≥1)

**Input:** `[(year, count), ...]`. Output: max of `year[i].count + year[i+1].count` for adjacent years.

### Approach 1 — sort + adjacent sum
```python
def max_consecutive(workshops):
    s = sorted(workshops)
    best = 0
    for i in range(len(s)-1):
        total = s[i][1] + s[i+1][1]
        if total > best:
            best = total
    return best
```

### Approach 2 — groupby year
```python
from collections import defaultdict
def max_consecutive(workshops):
    by_year = defaultdict(int)
    for y, c in workshops:
        by_year[y] += c
    years = sorted(by_year.keys())
    best = 0
    for i in range(len(years)-1):
        y = years[i]
        ny = years[i+1]
        total = by_year[y] + by_year[ny]
        if total > best:
            best = total
    return best
```

### Approach 3 — pandas
```python
import pandas as pd
def max_consecutive(workshops):
    rows = []
    for y, c in workshops:
        rows.append({'year': y, 'count': c})
    df = pd.DataFrame(rows)
    grouped = df.groupby('year')['count'].sum().sort_index()
    shifted = grouped.shift(-1)
    added = grouped + shifted
    return int(added.max())
```

### Approach 4 — numpy
```python
import numpy as np
def max_consecutive(workshops):
    by_year = {}
    for y, c in workshops:
        by_year[y] = by_year.get(y, 0) + c
    years = sorted(by_year.keys())
    counts_list = []
    for y in years:
        counts_list.append(by_year[y])
    counts = np.array(counts_list)
    pairs = counts[:-1] + counts[1:]
    best = 0
    for v in pairs:
        if v > best:
            best = v
    return int(best)
```

### Approach 5 — dict + list comprehension
```python
def max_consecutive(workshops):
    by_year = {}
    for y, c in workshops:
        by_year[y] = by_year.get(y, 0) + c
    years = sorted(by_year.keys())
    best = 0
    for i in range(len(years)-1):
        total = by_year[years[i]] + by_year[years[i+1]]
        if total > best:
            best = total
    return best
```

### Approach 6 — sliding window
```python
def max_consecutive(workshops):
    by_year = {}
    for y, c in workshops:
        by_year[y] = by_year.get(y, 0) + c
    counts = []
    for y in sorted(by_year.keys()):
        counts.append(by_year[y])
    best = 0
    for i in range(len(counts)-1):
        total = counts[i] + counts[i+1]
        if total > best:
            best = total
    return best
```

### Approach 7 — reduce
```python
from functools import reduce
def max_consecutive(workshops):
    by_year = reduce(
        lambda d, t: {**d, t[0]: d.get(t[0], 0) + t[1]},
        workshops,
        {}
    )
    counts = []
    for y in sorted(by_year.keys()):
        counts.append(by_year[y])
    best = 0
    for i in range(len(counts)-1):
        total = counts[i] + counts[i+1]
        if total > best:
            best = total
    return best
```

### Approach 8 — Counter + sorted
```python
from collections import Counter
def max_consecutive(workshops):
    c = Counter()
    for y, n in workshops:
        c[y] += n
    counts = []
    for y in sorted(c.keys()):
        counts.append(c[y])
    best = 0
    for i in range(len(counts)-1):
        total = counts[i] + counts[i+1]
        if total > best:
            best = total
    return best
```

### Approach 9 — generator
```python
def max_consecutive(workshops):
    by_year = {}
    for y, n in workshops:
        by_year[y] = by_year.get(y, 0) + n
    counts = []
    for y in sorted(by_year.keys()):
        counts.append(by_year[y])
    pairs = (counts[i] + counts[i+1] for i in range(len(counts)-1))
    best = 0
    for v in pairs:
        if v > best:
            best = v
    yield best
```

### Approach 10 — dict comprehension
```python
def max_consecutive(workshops):
    by_year = {}
    for y, _ in workshops:
        total = 0
        for yy, c in workshops:
            if yy == y:
                total += c
        by_year[y] = total
    counts = []
    for y in sorted(by_year.keys()):
        counts.append(by_year[y])
    best = 0
    for i in range(len(counts)-1):
        total = counts[i] + counts[i+1]
        if total > best:
            best = total
    return best
```

**Best:** Approach 1 or 3 (pandas shift trick).

---

## Problem 24 — Smallest number from digits of N (no leading zeros)

**Input:** N (int, positive or negative). Output: smallest number by rearranging digits, no leading zeros.

### Approach 1 — sort asc, but put smallest non-zero first
```python
def smallest(n):
    s = str(abs(n))
    s_list = []
    for c in s:
        s_list.append(c)
    s_list.sort()
    if s_list[0] != '0':
        out = ''
        for c in s_list:
            out += c
        return int(out)
    for i, c in enumerate(s_list):
        if c != '0':
            s_list[0], s_list[i] = s_list[i], s_list[0]
            break
    out = ''
    for c in s_list:
        out += c
    return int(out)
```

### Approach 2 — count zeros, place one non-zero first
```python
def smallest(n):
    s = str(abs(n))
    zeros = 0
    nonzeros = []
    for c in s:
        if c == '0':
            zeros += 1
        else:
            nonzeros.append(c)
    nonzeros.sort()
    if not nonzeros:
        return 0
    out = nonzeros[0] + '0' * zeros
    for c in nonzeros[1:]:
        out += c
    return int(out)
```

### Approach 3 — Counter
```python
from collections import Counter
def smallest(n):
    s = str(abs(n))
    c = Counter(s)
    if c['0'] == len(s):
        return 0
    first = None
    for ch in sorted(c):
        if ch != '0':
            first = ch
            break
    c[first] -= 1
    if c[first] == 0:
        del c[first]
    out = first
    for d in '0123456789':
        if d in c:
            out += d * c[d]
    return int(out)
```

### Approach 4 — bucket sort
```python
def smallest(n):
    s = str(abs(n))
    buckets = []
    for _ in range(10):
        buckets.append([])
    for c in s:
        buckets[int(c)].append(c)
    first_digit = None
    for d in range(1, 10):
        if buckets[d]:
            first_digit = d
            break
    buckets[first_digit].pop()
    zeros_part = '0' * len(buckets[0])
    rest = ''
    for d in range(1, 10):
        for _ in range(len(buckets[d])):
            rest += str(d)
    return int(str(first_digit) + zeros_part + rest)
```

### Approach 5 — pandas
```python
import pandas as pd
def smallest(n):
    s_list = []
    for c in str(abs(n)):
        s_list.append(c)
    s = pd.Series(s_list)
    sorted_list = []
    for v in s.sort_values():
        sorted_list.append(v)
    if sorted_list[0] != '0':
        out = ''
        for c in sorted_list:
            out += c
        return int(out)
    nz = None
    for i, c in enumerate(sorted_list):
        if c != '0':
            nz = i
            break
    sorted_list[0], sorted_list[nz] = sorted_list[nz], sorted_list[0]
    out = ''
    for c in sorted_list:
        out += c
    return int(out)
```

### Approach 6 — sorted + first non-zero
```python
def smallest(n):
    s = str(abs(n))
    s_list = []
    for c in s:
        s_list.append(c)
    s_list.sort()
    for i, c in enumerate(s_list):
        if c != '0':
            first = s_list.pop(i)
            s_list.insert(0, first)
            break
    out = ''
    for c in s_list:
        out += c
    return int(out)
```

### Approach 7 — heap + manual
```python
import heapq
def smallest(n):
    s = str(abs(n))
    digits = []
    for c in s:
        digits.append(c)
    heapq.heapify(digits)
    sorted_digits = []
    while digits:
        sorted_digits.append(heapq.heappop(digits))
    if sorted_digits[0] != '0':
        out = ''
        for d in sorted_digits:
            out += d
        return int(out)
    for i in range(len(sorted_digits)):
        if sorted_digits[i] != '0':
            sorted_digits[0], sorted_digits[i] = sorted_digits[i], sorted_digits[0]
            out = ''
            for d in sorted_digits:
                out += d
            return int(out)
    return 0
```

### Approach 8 — numpy
```python
import numpy as np
def smallest(n):
    s = str(abs(n))
    arr_list = []
    for c in s:
        arr_list.append(c)
    arr = np.array(arr_list)
    sorted_arr = np.sort(arr)
    sorted_list = []
    for v in sorted_arr:
        sorted_list.append(str(v))
    if sorted_list[0] != '0':
        out = ''
        for d in sorted_list:
            out += d
        return int(out)
    nz = None
    for i, c in enumerate(sorted_list):
        if c != '0':
            nz = i
            break
    sorted_list[0], sorted_list[nz] = sorted_list[nz], sorted_list[0]
    out = ''
    for d in sorted_list:
        out += d
    return int(out)
```

### Approach 9 — string replace
```python
def smallest(n):
    s = str(abs(n))
    if '0' not in s:
        sorted_s = []
        for c in s:
            sorted_s.append(c)
        sorted_s.sort()
        out = ''
        for c in sorted_s:
            out += c
        return int(out)
    sorted_s = []
    for c in s:
        sorted_s.append(c)
    sorted_s.sort()
    nz = None
    nz_val = None
    for c in sorted_s:
        if c != '0':
            nz = sorted_s.index(c)
            nz_val = c
            break
    sorted_s[0], sorted_s[nz] = sorted_s[nz], sorted_s[0]
    out = ''
    for c in sorted_s:
        out += c
    return int(out)
```

### Approach 10 — reduce
```python
from functools import reduce
def smallest(n):
    s = str(abs(n))
    s_list = []
    for c in s:
        s_list.append(c)
    s_list.sort()
    def step(acc, c):
        if not acc and c == '0':
            return acc + [c]
        if not acc:
            return [c] + acc
        return acc + [c]
    result = reduce(step, s_list, [])
    out = ''
    for c in result:
        out += c
    return int(out)
```

**Best:** Approach 2 — count zeros + smallest non-zero first. O(n).
