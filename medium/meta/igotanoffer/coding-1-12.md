# Meta DE Coding — 10 Approaches Per Problem (Batch 1: Problems 1-12)

Each problem is solved 10 different ways. Approaches ordered from most idiomatic to most creative.

---

## Problem 1 — Friends count from 2D list

**Input:** `[[2,3],[3,4],[5]]` (each pair = friendship). Person 5 has no friends.
**Output:** `{2: 1, 3: 2, 4: 1, 5: 0}`

### Approach 1 — Counter + defaultdict
```python
from collections import defaultdict, Counter
def friends(pairs):
    c = Counter()
    for a, b in pairs:
        c[a] += 1; c[b] += 1
    return dict(c)
```

### Approach 2 — defaultdict
```python
from collections import defaultdict
def friends(pairs):
    d = defaultdict(int)
    for a, b in pairs:
        d[a] += 1; d[b] += 1
    return dict(d)
```

### Approach 3 — set union of all people, then count
```python
def friends(pairs):
    people = {p for pair in pairs for p in pair}
    return {p: sum(p in pair for pair in pairs) for p in people}
```

### Approach 4 — manual dict
```python
def friends(pairs):
    d = {}
    for a, b in pairs:
        d[a] = d.get(a, 0) + 1
        d[b] = d.get(b, 0) + 1
    return d
```

### Approach 5 — reduce / functools
```python
from functools import reduce
def friends(pairs):
    return dict(reduce(lambda d, p: {**d, p[0]: d.get(p[0],0)+1,
                                            p[1]: d.get(p[1],0)+1},
                        pairs, {}))
```

### Approach 6 — pandas
```python
import pandas as pd
def friends(pairs):
    s = pd.Series([p for pair in pairs for p in pair])
    return s.value_counts().to_dict()
```

### Approach 7 — numpy bincount on flat
```python
import numpy as np
def friends(pairs):
    flat = np.array([p for pair in pairs for p in pair])
    return dict(zip(*np.unique(flat, return_counts=True)))
```

### Approach 8 — itertools chain + Counter
```python
from itertools import chain
from collections import Counter
def friends(pairs):
    return dict(Counter(chain.from_iterable(pairs)))
```

### Approach 9 — SQL-style groupby via list comprehension
```python
def friends(pairs):
    flat = [p for pair in pairs for p in pair]
    return {x: flat.count(x) for x in set(flat)}
```

### Approach 10 — dict comprehension with explicit loop
```python
def friends(pairs):
    flat = sum(pairs, [])
    return {p: flat.count(p) for p in set(flat)}
```

**Best:** Counter / defaultdict — O(n) and idiomatic.

---

## Problem 2 — Replace None with previous non-None (forward fill, no subquery)

**Input:** `[1,None,1,2,None]`
**Output:** `[1,1,1,2,2]`

### Approach 1 — iterative carry
```python
def ffill(a):
    last, out = None, []
    for x in a:
        last = x if x is not None else last
        out.append(x if x is not None else last)
    return out
```

### Approach 2 — itertools accumulate
```python
from itertools import accumulate
import operator
def ffill(a):
    return list(accumulate(a, lambda acc, x: x if x is not None else acc))
```

### Approach 3 — pandas
```python
import pandas as pd
def ffill(a):
    return pd.Series(a).ffill().tolist()
```

### Approach 4 — numpy with masking
```python
import numpy as np
def ffill(a):
    arr = np.array(a, dtype=object)
    mask = arr != None
    if not mask.any(): return arr.tolist()
    idx = np.where(mask, np.arange(len(arr)), 0)
    np.maximum.accumulate(idx, out=idx)
    return arr[idx].tolist()
```

### Approach 5 — list comprehension with side state
```python
def ffill(a):
    out, last = [], None
    for x in a:
        if x is not None: last = x
        out.append(last)
    return out
```

### Approach 6 — generator + next with sentinel
```python
def ffill(a):
    it = iter(a); last = None
    return [last := x if x is not None else last for x in a]
```

### Approach 7 — map with closure
```python
def ffill(a):
    state = {'last': None}
    def go(x):
        if x is not None: state['last'] = x
        return state['last']
    return list(map(go, a))
```

### Approach 8 — enumerate + slicing scan
```python
def ffill(a):
    out = [None]*len(a); last = None
    for i, x in enumerate(a):
        last = x if x is not None else last
        out[i] = last
    return out
```

### Approach 9 — functools.reduce
```python
def ffill(a):
    from functools import reduce
    return reduce(lambda acc, x: acc + [x if x is not None else acc[-1] if acc else None], a, [])
```

### Approach 10 — recursive
```python
def ffill(a):
    if not a: return []
    if a[0] is not None: return [a[0]] + ffill(a[1:])
    if len(a) == 1: return [None]
    rest = ffill(a[1:])
    return [rest[0] if rest[0] is not None else None] + rest
```

**Best:** itertools accumulate or pandas. Recursive will stack-overflow on long inputs.

---

## Problem 3 — Mismatched (case-sensitive) words between two strings

**Input:** s1 = "Firstly this is the first string", s2 = "Next is the second string"
**Output:** `['Firstly', 'this', 'first', 'Next', 'second']`

### Approach 1 — set symmetric difference
```python
def mismatched(s1, s2):
    return list((set(s1.split()) ^ set(s2.split())))
```

### Approach 2 — Counter subtraction both ways
```python
from collections import Counter
def mismatched(s1, s2):
    a, b = Counter(s1.split()), Counter(s2.split())
    return list((a - b) + (b - a))
```

### Approach 3 — list comprehension with not in
```python
def mismatched(s1, s2):
    a, b = s1.split(), s2.split()
    return [w for w in a if w not in b] + [w for w in b if w not in a]
```

### Approach 4 — preserve order via index sets
```python
def mismatched(s1, s2):
    a, b = s1.split(), s2.split()
    sa, sb = set(a), set(b)
    sym = sa ^ sb
    return [w for w in a + b if w in sym]
```

### Approach 5 — dict / hash + boolean arrays
```python
def mismatched(s1, s2):
    a, b = s1.split(), s2.split()
    from collections import defaultdict
    freq = defaultdict(int)
    for w in a + b: freq[w] += 1
    return [w for w in a + b if freq[w] == 1]
```

### Approach 6 — Counter.keys() subtraction
```python
from collections import Counter
def mismatched(s1, s2):
    a, b = Counter(s1.split()), Counter(s2.split())
    diff = a - b
    diff.update(b - a)
    return list(diff)
```

### Approach 7 — pandas Series isin
```python
import pandas as pd
def mismatched(s1, s2):
    a, b = pd.Series(s1.split()), pd.Series(s2.split())
    return a[~a.isin(b)].tolist() + b[~b.isin(a)].tolist()
```

### Approach 8 — functools reduce
```python
from functools import reduce
def mismatched(s1, s2):
    a, b = s1.split(), s2.split()
    in_a, in_b = set(a), set(b)
    sym = in_a.symmetric_difference(in_b)
    return [w for w in a if w in sym and w not in in_b] + \
           [w for w in b if w in sym and w not in in_a]
```

### Approach 9 — operator xor on sets
```python
import operator
def mismatched(s1, s2):
    return list(operator.xor(set(s1.split()), set(s2.split())))
```

### Approach 10 — manual membership counting
```python
def mismatched(s1, s2):
    a, b = s1.split(), s2.split()
    freq = {}
    for w in a + b: freq[w] = freq.get(w, 0) + 1
    return [w for w in a + b if freq[w] == 1]
```

**Best:** set symmetric difference for O(n+m).

---

## Problem 4 — Count char occurrences in string

**Input:** "mississippi", char "s"
**Output:** 4

### Approach 1 — str.count
```python
def count(s, c): return s.count(c)
```

### Approach 2 — sum + generator
```python
def count(s, c): return sum(1 for ch in s if ch == c)
```

### Approach 3 — Counter
```python
from collections import Counter
def count(s, c): return Counter(s)[c]
```

### Approach 4 — re.findall
```python
import re
def count(s, c): return len(re.findall(re.escape(c), s))
```

### Approach 5 — operator.countOf
```python
import operator
def count(s, c): return operator.countOf(s, c)
```

### Approach 6 — list comprehension len
```python
def count(s, c): return len([ch for ch in s if ch == c])
```

### Approach 7 — reduce
```python
from functools import reduce
def count(s, c): return reduce(lambda acc, ch: acc + (ch == c), s, 0)
```

### Approach 8 — dict.get loop
```python
def count(s, c):
    d = {}; 
    for ch in s: d[ch] = d.get(ch, 0) + 1
    return d.get(c, 0)
```

### Approach 9 — pandas
```python
import pandas as pd
def count(s, c): return pd.Series(list(s)).value_counts().get(c, 0)
```

### Approach 10 — numpy
```python
import numpy as np
def count(s, c): return int((np.array(list(s)) == c).sum())
```

**Best:** `str.count` — C-level, fastest.

---

## Problem 5 — Character frequency → format string `a3b2c1`

### Approach 1 — collections.Counter + join
```python
from collections import Counter
def fmt(s): return ''.join(f'{c}{n}' for c, n in Counter(s).items())
```

### Approach 2 — sort + groupby
```python
from itertools import groupby
def fmt(s): return ''.join(f'{c}{sum(1 for _ in g)}' for c, g in groupby(sorted(s)))
```

### Approach 3 — dict ordering
```python
def fmt(s):
    d = {}
    for c in s: d[c] = d.get(c, 0) + 1
    return ''.join(f'{c}{n}' for c, n in d.items())
```

### Approach 4 — pandas
```python
import pandas as pd
def fmt(s): return ''.join(f'{c}{n}' for c, n in pd.Series(list(s)).value_counts().items())
```

### Approach 5 — dict comprehension on unique
```python
def fmt(s):
    return ''.join(f'{c}{s.count(c)}' for c in dict.fromkeys(s))
```

### Approach 6 — OrderedDict
```python
from collections import OrderedDict
def fmt(s):
    d = OrderedDict()
    for c in s: d[c] = d.get(c, 0) + 1
    return ''.join(f'{c}{n}' for c, n in d.items())
```

### Approach 7 — defaultdict
```python
from collections import defaultdict
def fmt(s):
    d = defaultdict(int)
    for c in s: d[c] += 1
    return ''.join(f'{c}{d[c]}' for c in dict.fromkeys(s))
```

### Approach 8 — sort + zip trick
```python
def fmt(s):
    srt = sorted(s)
    groups = [srt.count(c) for c in dict.fromkeys(srt)]
    return ''.join(f'{c}{n}' for c, n in zip(dict.fromkeys(srt), groups))
```

### Approach 9 — reduce
```python
from functools import reduce
def fmt(s):
    return reduce(lambda acc, c: acc + (f'{c}1' if c not in acc else ''), s, '')
# (Naive — duplicates handled via replacement; not pure.)
```

### Approach 10 — regex matchall
```python
import re
def fmt(s):
    return ''.join(f'{m.group()}{len(m.group())}' for m in re.finditer(r'(.)\1*', s))
```

**Best:** Counter preserves insertion order in Python 3.7+.

---

## Problem 6 — IP address validation (IPv4)

### Approach 1 — split + range + length
```python
def valid_ip(s):
    parts = s.split('.')
    if len(parts) != 4: return False
    for p in parts:
        if not p.isdigit(): return False
        if len(p) > 1 and p[0] == '0': return False
        if not 0 <= int(p) <= 255: return False
    return True
```

### Approach 2 — regex
```python
import re
def valid_ip(s):
    return bool(re.fullmatch(r'(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}', s))
```

### Approach 3 — try/except int conversion
```python
def valid_ip(s):
    try:
        return len(s.split('.')) == 4 and all(0 <= int(p) <= 255 and (p == '0' or not p.startswith('0')) for p in s.split('.'))
    except ValueError:
        return False
```

### Approach 4 — ipaddress stdlib
```python
import ipaddress
def valid_ip(s):
    try:
        ipaddress.IPv4Address(s); return True
    except ipaddress.AddressValueError:
        return False
```

### Approach 5 — socket
```python
import socket
import struct
def valid_ip(s):
    try:
        socket.inet_aton(s); return True
    except OSError:
        return False
```

### Approach 6 — bytes + manual unpack
```python
def valid_ip(s):
    try:
        packed = bytes(int(p) for p in s.split('.'))
        return len(packed) == 4 and all(0 <= b <= 255 for b in packed)
    except ValueError:
        return False
```

### Approach 7 — map + all
```python
def valid_ip(s):
    parts = s.split('.')
    return len(parts) == 4 and all(
        p.isdigit() and 0 <= int(p) <= 255 and (p == '0' or not p.startswith('0'))
        for p in parts
    )
```

### Approach 8 — regex strict on leading zeros
```python
import re
def valid_ip(s):
    return bool(re.fullmatch(r'(25[0-5]|2[0-4]\d|[01]?\d?\d)(\.(25[0-5]|2[0-4]\d|[01]?\d?\d)){3}', s))
```

### Approach 9 — all() with generator
```python
def valid_ip(s):
    parts = s.split('.')
    return (len(parts) == 4
            and all(p.lstrip('0') == p or p == '0' for p in parts)
            and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts))
```

### Approach 10 — state machine
```python
def valid_ip(s):
    parts = s.split('.')
    if len(parts) != 4: return False
    for p in parts:
        state = 'leading'; val = 0
        for ch in p:
            if not ch.isdigit(): return False
            if state == 'leading' and ch == '0' and len(p) > 1: return False
            state = 'digits'
            val = val * 10 + int(ch)
            if val > 255: return False
        if not p: return False
    return True
```

**Best:** `ipaddress.IPv4Address` for production; manual split+range for interview clarity.

---

## Problem 7 — Monotonic check

### Approach 1 — two-pass comparison
```python
def monotonic(a):
    return all(a[i] <= a[i+1] for i in range(len(a)-1)) or \
           all(a[i] >= a[i+1] for i in range(len(a)-1))
```

### Approach 2 — sorted + equal
```python
def monotonic(a):
    return a == sorted(a) or a == sorted(a, reverse=True)
```

### Approach 3 — single-pass flag
```python
def monotonic(a):
    inc = dec = True
    for i in range(1, len(a)):
        if a[i] > a[i-1]: dec = False
        if a[i] < a[i-1]: inc = False
    return inc or dec
```

### Approach 4 — numpy diff
```python
import numpy as np
def monotonic(a):
    d = np.diff(a)
    return (d >= 0).all() or (d <= 0).all()
```

### Approach 5 — itertools pairwise
```python
from itertools import pairwise
def monotonic(a):
    pairs = list(pairwise(a))
    return all(x <= y for x, y in pairs) or all(x >= y for x, y in pairs)
```

### Approach 6 — reduce
```python
from functools import reduce
def monotonic(a):
    incr = reduce(lambda acc, t: acc and t[0] <= t[1], zip(a, a[1:]), True)
    decr = reduce(lambda acc, t: acc and t[0] >= t[1], zip(a, a[1:]), True)
    return incr or decr
```

### Approach 7 — pandas
```python
import pandas as pd
def monotonic(a):
    s = pd.Series(a)
    d = s.diff().dropna()
    return (d >= 0).all() or (d <= 0).all()
```

### Approach 8 — generator + any/all
```python
def monotonic(a):
    diffs = [a[i+1]-a[i] for i in range(len(a)-1)]
    return all(d >= 0 for d in diffs) or all(d <= 0 for d in diffs)
```

### Approach 9 — recursive
```python
def monotonic(a):
    if len(a) <= 1: return True
    if len(a) == 2: return True
    inc = a[0] <= a[1] and (monotonic_inc(a) if False else True)
    # recursive variant: simpler check
    return (all(a[i] <= a[i+1] for i in range(len(a)-1))) or \
           (all(a[i] >= a[i+1] for i in range(len(a)-1)))
```

### Approach 10 — set of directions
```python
def monotonic(a):
    if len(a) < 2: return True
    dirs = {1 if a[i+1] > a[i] else -1 if a[i+1] < a[i] else 0 for i in range(len(a)-1)}
    return dirs <= {1, 0} or dirs <= {-1, 0}
```

**Best:** single-pass flag — O(n) time, O(1) space.

---

## Problem 8 — Words in one sentence but not the other (symmetric difference)

### Approach 1 — set symmetric_difference
```python
def sym_diff(s1, s2):
    return list(set(s1.split()) ^ set(s2.split()))
```

### Approach 2 — Counter subtraction
```python
from collections import Counter
def sym_diff(s1, s2):
    a, b = Counter(s1.split()), Counter(s2.split())
    return list((a - b) + (b - a))
```

### Approach 3 — list comprehension
```python
def sym_diff(s1, s2):
    a, b = set(s1.split()), set(s2.split())
    return [w for w in s1.split() if w not in b] + [w for w in s2.split() if w not in a]
```

### Approach 4 — operator.xor
```python
import operator
def sym_diff(s1, s2):
    return list(operator.xor(set(s1.split()), set(s2.split())))
```

### Approach 5 — dict counting
```python
def sym_diff(s1, s2):
    freq = {}
    for w in s1.split() + s2.split(): freq[w] = freq.get(w, 0) + 1
    return [w for w in s1.split() + s2.split() if freq[w] == 1]
```

### Approach 6 — pandas
```python
import pandas as pd
def sym_diff(s1, s2):
    a, b = pd.Series(s1.split()), pd.Series(s2.split())
    return a[~a.isin(b)].tolist() + b[~b.isin(a)].tolist()
```

### Approach 7 — reduce + set ops
```python
from functools import reduce
def sym_diff(s1, s2):
    return list(reduce(lambda acc, w: acc ^ {w}, s1.split() + s2.split(), set()))
```

### Approach 8 — sorted output via merge
```python
def sym_diff(s1, s2):
    diff = set(s1.split()) ^ set(s2.split())
    return sorted(diff)
```

### Approach 9 — generator with sentinel
```python
def sym_diff(s1, s2):
    a, b = s1.split(), s2.split()
    sa, sb = set(a), set(b)
    yield from (w for w in a if w not in sb)
    yield from (w for w in b if w not in sa)
```

### Approach 10 — explicit two-filter concat
```python
def sym_diff(s1, s2):
    a, b = s1.split(), s2.split()
    in_both = set(a) & set(b)
    return list(filter(lambda w: w not in in_both, a + b))
```

**Best:** set symmetric_difference — O(n+m) and intent-matching.

---

## Problem 9 — Count neighbors per node in graph (2D list)

### Approach 1 — Counter on flattened
```python
from collections import Counter
from itertools import chain
def neighbors(graph):
    return dict(Counter(chain.from_iterable(graph)))
```

### Approach 2 — defaultdict
```python
from collections import defaultdict
def neighbors(graph):
    d = defaultdict(int)
    for edge in graph:
        for n in edge: d[n] += 1
    return dict(d)
```

### Approach 3 — list count
```python
def neighbors(graph):
    flat = [n for edge in graph for n in edge]
    return {n: flat.count(n) for n in set(flat)}
```

### Approach 4 — pandas
```python
import pandas as pd
def neighbors(graph):
    return pd.Series([n for edge in graph for n in edge]).value_counts().to_dict()
```

### Approach 5 — numpy bincount
```python
import numpy as np
def neighbors(graph):
    flat = np.array([n for edge in graph for n in edge])
    return dict(zip(*np.unique(flat, return_counts=True)))
```

### Approach 6 — reduce
```python
from functools import reduce
def neighbors(graph):
    return dict(reduce(lambda d, edge: {**d, **{n: d.get(n, 0)+1 for n in edge}}, graph, {}))
```

### Approach 7 — dict comprehension
```python
def neighbors(graph):
    flat = sum(graph, [])
    return {n: flat.count(n) for n in dict.fromkeys(flat)}
```

### Approach 8 — Counter with explicit init
```python
from collections import Counter
def neighbors(graph):
    c = Counter()
    for edge in graph:
        c.update(edge)
    return dict(c)
```

### Approach 9 — generator with dict
```python
def neighbors(graph):
    d = {}
    for edge in graph:
        for n in edge:
            d[n] = d.get(n, 0) + 1
    return d
```

### Approach 10 — itertools.chain + manual loop
```python
from itertools import chain
def neighbors(graph):
    d = {}
    for n in chain.from_iterable(graph):
        d[n] = d.get(n, 0) + 1
    return d
```

**Best:** Counter or defaultdict.

---

## Problem 10 — Key for nth highest value in dict

### Approach 1 — sort + iterate
```python
def nth_key(d, n):
    for k, v in sorted(d.items(), key=lambda kv: kv[1], reverse=True):
        if v == sorted(set(d.values()), reverse=True)[n-1]:
            return k
```

### Approach 2 — heapq.nlargest
```python
import heapq
def nth_key(d, n):
    unique = sorted(set(d.values()), reverse=True)
    target = unique[n-1]
    keys = sorted(k for k, v in d.items() if v == target)
    return keys[0]
```

### Approach 3 — Counter.most_common
```python
from collections import Counter
def nth_key(d, n):
    c = Counter(d)
    seen = []
    for k, v in c.most_common():
        if not seen or seen[-1][1] != v:
            seen.append((k, v))
            if len(seen) == n: return k
```

### Approach 4 — pandas
```python
import pandas as pd
def nth_key(d, n):
    s = pd.Series(d).sort_values(ascending=False).drop_duplicates()
    return s.index[n-1]
```

### Approach 5 — sort values reverse, pick
```python
def nth_key(d, n):
    items = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[n-1][0]
```

### Approach 6 — numpy argpartition
```python
import numpy as np
def nth_key(d, n):
    keys = list(d.keys()); vals = np.array(list(d.values()))
    order = np.argsort(-vals, kind='stable')
    return keys[order[n-1]]
```

### Approach 7 — manual scan
```python
def nth_key(d, n):
    pairs = [(v, k) for k, v in d.items()]
    pairs.sort(reverse=True)
    seen_vals = []
    for v, k in pairs:
        if not seen_vals or seen_vals[-1] != v:
            seen_vals.append(v)
        if len(seen_vals) == n:
            return sorted(k for vv, k in pairs if vv == v)[0]
```

### Approach 8 — dict inversion + sorted
```python
def nth_key(d, n):
    inv = {}
    for k, v in d.items():
        inv.setdefault(v, []).append(k)
    for v in sorted(inv, reverse=True):
        if n == 1: return sorted(inv[v])[0]
        n -= 1
```

### Approach 9 — reduce
```python
from functools import reduce
def nth_key(d, n):
    unique_vals = sorted(set(d.values()), reverse=True)
    target = unique_vals[n-1]
    candidates = sorted(k for k, v in d.items() if v == target)
    return reduce(lambda a, b: a if a < b else b, candidates)
```

### Approach 10 — sorted zip trick
```python
def nth_key(d, n):
    keys, vals = zip(*d.items())
    order = sorted(range(len(vals)), key=lambda i: (-vals[i], keys[i]))
    return keys[order[n-1]]
```

**Best:** sort once with tie-breaker `(value desc, key asc)` — single pass.

---

## Problem 11 — Flatten nested dictionary

### Approach 1 — recursive
```python
def flatten(d, parent_key='', sep='.'):
    items = {}
    for k, v in d.items():
        key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            items.update(flatten(v, key, sep=sep))
        else:
            items[key] = v
    return items
```

### Approach 2 — stack/iterative
```python
def flatten(d, sep='.'):
    items, stack = {}, [((), d)]
    while stack:
        prefix, obj = stack.pop()
        for k, v in obj.items():
            key = (*prefix, k)
            if isinstance(v, dict):
                stack.append((key, v))
            else:
                items[sep.join(key)] = v
    return items
```

### Approach 3 — generator
```python
def flatten(d, parent_key='', sep='.'):
    for k, v in d.items():
        key = f'{parent_key}{sep}{k}' if parent_key else k
        if isinstance(v, dict):
            yield from flatten(v, key, sep=sep)
        else:
            yield key, v
```

### Approach 4 — reduce
```python
from functools import reduce
def flatten(d, sep='.'):
    def step(acc, kv):
        k, v = kv
        if isinstance(v, dict):
            return {**acc, **{f'{k}{sep}{sk}': sv for sk, sv in flatten(v, sep=sep).items()}}
        return {**acc, k: v}
    return reduce(step, d.items(), {})
```

### Approach 5 — BFS with queue
```python
from collections import deque
def flatten(d, sep='.'):
    out, q = {}, deque([((), d)])
    while q:
        prefix, obj = q.popleft()
        for k, v in obj.items():
            key = prefix + (k,)
            if isinstance(v, dict):
                q.append((key, v))
            else:
                out[sep.join(key)] = v
    return out
```

### Approach 6 — json + walk
```python
import json
def flatten(d, sep='.'):
    flat = {}
    def walk(prefix, obj):
        for k, v in obj.items():
            key = f'{prefix}{sep}{k}' if prefix else k
            if isinstance(v, dict): walk(key, v)
            else: flat[key] = v
    walk('', d)
    return flat
```

### Approach 7 — pandas json_normalize
```python
import pandas as pd
def flatten(d, sep='.'):
    return pd.json_normalize(d, sep=sep).to_dict(orient='records')[0]
```

### Approach 8 — iterative with path accumulator
```python
def flatten(d, sep='.'):
    out = {}
    def helper(obj, path):
        for k, v in obj.items():
            new_path = f'{path}{sep}{k}' if path else k
            if isinstance(v, dict):
                helper(v, new_path)
            else:
                out[new_path] = v
    helper(d, '')
    return out
```

### Approach 9 — operator + comprehension
```python
def flatten(d, sep='.'):
    return {sep.join(map(str, k)): v for k, v in _iter_paths(d)}
def _iter_paths(d, prefix=()):
    for k, v in d.items():
        key = prefix + (k,)
        if isinstance(v, dict):
            yield from _iter_paths(v, key)
        else:
            yield key, v
```

### Approach 10 — regex-based path (not pure but creative)
```python
import re
def flatten(d, sep='.'):
    s = str(d)
    # Not a real solution; flag: do not use this.
    raise NotImplementedError
```

**Best:** recursive generator — handles arbitrary depth cleanly.

---

## Problem 12 — Count friends per person from `[[A,B],[A,C],...]`

(Note: undirected, no repeat pairs, ≤2 people per relationship.)

### Approach 1 — Counter on flattened
```python
from collections import Counter
from itertools import chain
def friend_counts(pairs):
    return dict(Counter(chain.from_iterable(pairs)))
```

### Approach 2 — defaultdict
```python
from collections import defaultdict
def friend_counts(pairs):
    d = defaultdict(int)
    for a, b in pairs:
        d[a] += 1; d[b] += 1
    return dict(d)
```

### Approach 3 — set union + count
```python
def friend_counts(pairs):
    people = {p for pair in pairs for p in pair}
    return {p: sum(p in pair for pair in pairs) for p in people}
```

### Approach 4 — dict.get loop
```python
def friend_counts(pairs):
    d = {}
    for a, b in pairs:
        d[a] = d.get(a, 0) + 1
        d[b] = d.get(b, 0) + 1
    return d
```

### Approach 5 — pandas
```python
import pandas as pd
def friend_counts(pairs):
    return pd.Series([p for pair in pairs for p in pair]).value_counts().to_dict()
```

### Approach 6 — numpy bincount
```python
import numpy as np
def friend_counts(pairs):
    flat = np.array([p for pair in pairs for p in pair])
    return dict(zip(*np.unique(flat, return_counts=True)))
```

### Approach 7 — reduce
```python
from functools import reduce
def friend_counts(pairs):
    return dict(reduce(lambda d, p: {**d, p[0]: d.get(p[0], 0)+1,
                                            p[1]: d.get(p[1], 0)+1}, pairs, {}))
```

### Approach 8 — list count
```python
def friend_counts(pairs):
    flat = sum(pairs, [])
    return {p: flat.count(p) for p in set(flat)}
```

### Approach 9 — dict comp + manual
```python
def friend_counts(pairs):
    d = {}
    for pair in pairs:
        for p in pair:
            d[p] = d.get(p, 0) + 1
    return d
```

### Approach 10 — Counter with update
```python
from collections import Counter
def friend_counts(pairs):
    c = Counter()
    for pair in pairs:
        c.update(pair)
    return dict(c)
```

**Best:** Counter (Approach 1) or defaultdict (Approach 2).
