# Meta DE Coding — 10 Approaches Per Problem (Batch 1: Problems 1-12)

Each problem is solved 10 different ways. Approaches ordered from most idiomatic to most creative.
All code uses explicit `for` loops with full step-by-step logic for clarity.

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
        c[a] += 1
        c[b] += 1
    result = {}
    for k, v in c.items():
        result[k] = v
    return result
```

### Approach 2 — defaultdict
```python
from collections import defaultdict
def friends(pairs):
    d = defaultdict(int)
    for a, b in pairs:
        d[a] += 1
        d[b] += 1
    result = {}
    for k, v in d.items():
        result[k] = v
    return result
```

### Approach 3 — set union of all people, then count
```python
def friends(pairs):
    people = set()
    for pair in pairs:
        for p in pair:
            people.add(p)
    result = {}
    for p in people:
        count = 0
        for pair in pairs:
            if p in pair:
                count += 1
        result[p] = count
    return result
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
    def step(d, pair):
        a, b = pair
        d[a] = d.get(a, 0) + 1
        d[b] = d.get(b, 0) + 1
        return d
    return reduce(step, pairs, {})
```

### Approach 6 — pandas
```python
import pandas as pd
def friends(pairs):
    all_people = []
    for pair in pairs:
        for p in pair:
            all_people.append(p)
    s = pd.Series(all_people)
    counts = s.value_counts()
    result = {}
    for k, v in counts.items():
        result[k] = int(v)
    return result
```

### Approach 7 — numpy bincount on flat
```python
import numpy as np
def friends(pairs):
    flat_list = []
    for pair in pairs:
        for p in pair:
            flat_list.append(p)
    arr = np.array(flat_list)
    unique, counts = np.unique(arr, return_counts=True)
    result = {}
    for i in range(len(unique)):
        result[int(unique[i])] = int(counts[i])
    return result
```

### Approach 8 — itertools chain + Counter
```python
from itertools import chain
from collections import Counter
def friends(pairs):
    all_people = list(chain.from_iterable(pairs))
    c = Counter(all_people)
    result = {}
    for k, v in c.items():
        result[k] = v
    return result
```

### Approach 9 — SQL-style groupby via list comprehension
```python
def friends(pairs):
    flat = []
    for pair in pairs:
        for p in pair:
            flat.append(p)
    unique = set(flat)
    result = {}
    for x in unique:
        result[x] = flat.count(x)
    return result
```

### Approach 10 — dict comprehension with explicit loop
```python
def friends(pairs):
    flat = []
    for pair in pairs:
        for p in pair:
            flat.append(p)
    unique = set(flat)
    result = {}
    for p in unique:
        result[p] = flat.count(p)
    return result
```

**Best:** Counter / defaultdict — O(n) and idiomatic.

---

## Problem 2 — Replace None with previous non-None (forward fill, no subquery)

**Input:** `[1,None,1,2,None]`
**Output:** `[1,1,1,2,2]`

### Approach 1 — full index loop with copy
```python
def ffill(a):
    out = list(a)
    for i in range(1, len(out)):
        if out[i] is None:
            out[i] = out[i-1]
    return out
```

### Approach 2 — itertools accumulate
```python
from itertools import accumulate
def ffill(a):
    def keep(acc, x):
        if x is not None:
            return x
        return acc
    out = []
    for value in accumulate(a, keep):
        out.append(value)
    return out
```

### Approach 3 — pandas
```python
import pandas as pd
def ffill(a):
    s = pd.Series(a)
    filled = s.ffill()
    out = []
    for v in filled:
        out.append(v)
    return out
```

### Approach 4 — numpy with masking
```python
import numpy as np
def ffill(a):
    arr = np.array(a, dtype=object)
    mask = arr != None
    if not mask.any():
        out = []
        for v in arr:
            out.append(v)
        return out
    idx = np.where(mask, np.arange(len(arr)), 0)
    np.maximum.accumulate(idx, out=idx)
    out = []
    for v in arr[idx]:
        out.append(v)
    return out
```

### Approach 5 — list comprehension with side state
```python
def ffill(a):
    out = []
    last = None
    for x in a:
        if x is not None:
            last = x
        out.append(last)
    return out
```

### Approach 6 — generator + next with sentinel
```python
def ffill(a):
    out = []
    last = None
    for x in a:
        if x is not None:
            last = x
        out.append(last)
    return out
```

### Approach 7 — map with closure
```python
def ffill(a):
    state = {'last': None}
    def go(x):
        if x is not None:
            state['last'] = x
        return state['last']
    out = []
    for value in map(go, a):
        out.append(value)
    return out
```

### Approach 8 — enumerate + slicing scan
```python
def ffill(a):
    out = [None] * len(a)
    last = None
    for i, x in enumerate(a):
        if x is not None:
            last = x
        out[i] = last
    return out
```

### Approach 9 — functools.reduce
```python
from functools import reduce
def ffill(a):
    def step(acc, x):
        if not acc:
            return [x if x is not None else None]
        prev = acc[-1] if acc[-1] is not None else None
        return acc + [x if x is not None else prev]
    return reduce(step, a, [])
```

### Approach 10 — recursive
```python
def ffill(a):
    if not a:
        return []
    if a[0] is not None:
        return [a[0]] + ffill(a[1:])
    if len(a) == 1:
        return [None]
    rest = ffill(a[1:])
    first = rest[0] if rest[0] is not None else None
    return [first] + rest
```

**Best:** itertools accumulate or pandas. Recursive will stack-overflow on long inputs.

---

## Problem 3 — Mismatched (case-sensitive) words between two strings

**Input:** s1 = "Firstly this is the first string", s2 = "Next is the second string"
**Output:** `['Firstly', 'this', 'first', 'Next', 'second']`

**Quick runnable example:**
```python
def mismatched(s1, s2):
    a = s1.split()
    b = s2.split()
    sa = set(a)
    sb = set(b)
    out = []
    for w in a:
        if w not in sb:
            out.append(w)
    for w in b:
        if w not in sa:
            out.append(w)
    return out

s1 = "Firstly this is the first string"
s2 = "Next is the second string"
print(mismatched(s1, s2))
# ['Firstly', 'this', 'first', 'Next', 'second']
```

### Approach 1 — set symmetric difference
```python
def mismatched(s1, s2):
    words1 = set(s1.split())
    words2 = set(s2.split())
    diff = words1 ^ words2
    out = []
    for w in diff:
        out.append(w)
    return out
```

### Approach 2 — Counter subtraction both ways
```python
from collections import Counter
def mismatched(s1, s2):
    a = Counter(s1.split())
    b = Counter(s2.split())
    only_a = a - b
    only_b = b - a
    combined = list(only_a.elements()) + list(only_b.elements())
    return combined
```

### Approach 3 — list comprehension with not in
```python
def mismatched(s1, s2):
    a = s1.split()
    b = s2.split()
    result = []
    for w in a:
        if w not in b:
            result.append(w)
    for w in b:
        if w not in a:
            result.append(w)
    return result
```

### Approach 4 — preserve order via index sets
```python
def mismatched(s1, s2):
    a = s1.split()
    b = s2.split()
    sa = set(a)
    sb = set(b)
    sym = sa ^ sb
    result = []
    for w in a + b:
        if w in sym:
            result.append(w)
    return result
```

### Approach 5 — dict / hash + boolean arrays
```python
from collections import defaultdict
def mismatched(s1, s2):
    a = s1.split()
    b = s2.split()
    freq = defaultdict(int)
    for w in a + b:
        freq[w] += 1
    result = []
    for w in a + b:
        if freq[w] == 1:
            result.append(w)
    return result
```

### Approach 6 — Counter.keys() subtraction
```python
from collections import Counter
def mismatched(s1, s2):
    a = Counter(s1.split())
    b = Counter(s2.split())
    diff = a - b
    diff.update(b - a)
    out = []
    for w in diff.elements():
        out.append(w)
    return out
```

### Approach 7 — pandas Series isin
```python
import pandas as pd
def mismatched(s1, s2):
    a = pd.Series(s1.split())
    b = pd.Series(s2.split())
    only_a = []
    for v in a[~a.isin(b)]:
        only_a.append(v)
    only_b = []
    for v in b[~b.isin(a)]:
        only_b.append(v)
    return only_a + only_b
```

### Approach 8 — functools reduce
```python
def mismatched(s1, s2):
    a = s1.split()
    b = s2.split()
    in_a = set(a)
    in_b = set(b)
    sym = in_a.symmetric_difference(in_b)
    result = []
    for w in a:
        if w in sym and w not in in_b:
            result.append(w)
    for w in b:
        if w in sym and w not in in_a:
            result.append(w)
    return result
```

### Approach 9 — operator xor on sets
```python
import operator
def mismatched(s1, s2):
    a = set(s1.split())
    b = set(s2.split())
    out = []
    for w in operator.xor(a, b):
        out.append(w)
    return out
```

### Approach 10 — manual membership counting
```python
def mismatched(s1, s2):
    a = s1.split()
    b = s2.split()
    freq = {}
    for w in a + b:
        freq[w] = freq.get(w, 0) + 1
    result = []
    for w in a + b:
        if freq[w] == 1:
            result.append(w)
    return result
```

**Best:** set symmetric difference for O(n+m).

---

## Problem 4 — Count char occurrences in string

**Input:** "mississippi", char "s"
**Output:** 4

### Approach 1 — str.count
```python
def count(s, c):
    return s.count(c)
```

### Approach 2 — sum + generator
```python
def count(s, c):
    total = 0
    for ch in s:
        if ch == c:
            total += 1
    return total
```

### Approach 3 — Counter
```python
from collections import Counter
def count(s, c):
    return Counter(s)[c]
```

### Approach 4 — re.findall
```python
import re
def count(s, c):
    return len(re.findall(re.escape(c), s))
```

### Approach 5 — operator.countOf
```python
import operator
def count(s, c):
    return operator.countOf(s, c)
```

### Approach 6 — list comprehension len
```python
def count(s, c):
    matches = []
    for ch in s:
        if ch == c:
            matches.append(ch)
    return len(matches)
```

### Approach 7 — reduce
```python
from functools import reduce
def count(s, c):
    def step(acc, ch):
        if ch == c:
            return acc + 1
        return acc
    return reduce(step, s, 0)
```

### Approach 8 — dict.get loop
```python
def count(s, c):
    d = {}
    for ch in s:
        d[ch] = d.get(ch, 0) + 1
    return d.get(c, 0)
```

### Approach 9 — pandas
```python
import pandas as pd
def count(s, c):
    chars = []
    for ch in s:
        chars.append(ch)
    counts = pd.Series(chars).value_counts()
    if c in counts:
        return int(counts[c])
    return 0
```

### Approach 10 — numpy
```python
import numpy as np
def count(s, c):
    arr = np.array(list(s))
    return int((arr == c).sum())
```

**Best:** `str.count` — C-level, fastest.

---

## Problem 5 — Character frequency → format string `a3b2c1`

**Input:** "aaabbc"
**Output:** "a3b2c1"

### Approach 1 — collections.Counter + join
```python
from collections import Counter
def fmt(s):
    c = Counter(s)
    parts = []
    for ch, n in c.items():
        parts.append(f'{ch}{n}')
    return ''.join(parts)
```

### Approach 2 — sort + groupby
```python
from itertools import groupby
def fmt(s):
    srt = sorted(s)
    parts = []
    for ch, group in groupby(srt):
        count = sum(1 for _ in group)
        parts.append(f'{ch}{count}')
    return ''.join(parts)
```

### Approach 3 — dict ordering
```python
def fmt(s):
    d = {}
    for c in s:
        d[c] = d.get(c, 0) + 1
    parts = []
    for c, n in d.items():
        parts.append(f'{c}{n}')
    return ''.join(parts)
```

### Approach 4 — pandas
```python
import pandas as pd
def fmt(s):
    counts = pd.Series(list(s)).value_counts()
    parts = []
    for ch, n in counts.items():
        parts.append(f'{ch}{n}')
    return ''.join(parts)
```

### Approach 5 — dict comprehension on unique
```python
def fmt(s):
    seen = []
    for c in s:
        if c not in seen:
            seen.append(c)
    parts = []
    for c in seen:
        parts.append(f'{c}{s.count(c)}')
    return ''.join(parts)
```

### Approach 6 — OrderedDict
```python
from collections import OrderedDict
def fmt(s):
    d = OrderedDict()
    for c in s:
        d[c] = d.get(c, 0) + 1
    parts = []
    for c, n in d.items():
        parts.append(f'{c}{n}')
    return ''.join(parts)
```

### Approach 7 — defaultdict
```python
from collections import defaultdict
def fmt(s):
    d = defaultdict(int)
    for c in s:
        d[c] += 1
    seen = []
    for c in s:
        if c not in seen:
            seen.append(c)
    parts = []
    for c in seen:
        parts.append(f'{c}{d[c]}')
    return ''.join(parts)
```

### Approach 8 — sort + zip trick
```python
def fmt(s):
    srt = sorted(s)
    seen = []
    for c in srt:
        if c not in seen:
            seen.append(c)
    groups = []
    for c in seen:
        groups.append(srt.count(c))
    parts = []
    for c, n in zip(seen, groups):
        parts.append(f'{c}{n}')
    return ''.join(parts)
```

### Approach 9 — reduce (track counts explicitly)
```python
from functools import reduce
def fmt(s):
    def step(acc, c):
        acc[c] = acc.get(c, 0) + 1
        return acc
    counts = reduce(step, s, {})
    parts = []
    for c, n in counts.items():
        parts.append(f'{c}{n}')
    return ''.join(parts)
```

### Approach 10 — regex matchall
```python
import re
def fmt(s):
    parts = []
    for m in re.finditer(r'(.)\1*', s):
        parts.append(f'{m.group()}{len(m.group())}')
    return ''.join(parts)
```

**Best:** Counter preserves insertion order in Python 3.7+.

---

## Problem 6 — IP address validation (IPv4)

### Approach 1 — split + range + length
```python
def valid_ip(s):
    parts = s.split('.')
    if len(parts) != 4:
        return False
    for p in parts:
        if not p.isdigit():
            return False
        if len(p) > 1 and p[0] == '0':
            return False
        if not (0 <= int(p) <= 255):
            return False
    return True
```

### Approach 2 — regex
```python
import re
def valid_ip(s):
    pattern = r'(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}'
    return bool(re.fullmatch(pattern, s))
```

### Approach 3 — try/except int conversion
```python
def valid_ip(s):
    try:
        parts = s.split('.')
        if len(parts) != 4:
            return False
        for p in parts:
            if not (0 <= int(p) <= 255):
                return False
            if p != '0' and p.startswith('0'):
                return False
        return True
    except ValueError:
        return False
```

### Approach 4 — ipaddress stdlib
```python
import ipaddress
def valid_ip(s):
    try:
        ipaddress.IPv4Address(s)
        return True
    except ipaddress.AddressValueError:
        return False
```

### Approach 5 — socket
```python
import socket
def valid_ip(s):
    try:
        socket.inet_aton(s)
        return True
    except OSError:
        return False
```

### Approach 6 — bytes + manual unpack
```python
def valid_ip(s):
    try:
        parts = s.split('.')
        packed = bytes(int(p) for p in parts)
        if len(packed) != 4:
            return False
        for b in packed:
            if not (0 <= b <= 255):
                return False
        return True
    except ValueError:
        return False
```

### Approach 7 — map + all
```python
def valid_ip(s):
    parts = s.split('.')
    if len(parts) != 4:
        return False
    for p in parts:
        if not p.isdigit():
            return False
        if not (0 <= int(p) <= 255):
            return False
        if p != '0' and p.startswith('0'):
            return False
    return True
```

### Approach 8 — regex strict on leading zeros
```python
import re
def valid_ip(s):
    pattern = r'(25[0-5]|2[0-4]\d|[01]?\d?\d)(\.(25[0-5]|2[0-4]\d|[01]?\d?\d)){3}'
    return bool(re.fullmatch(pattern, s))
```

### Approach 9 — all() with generator
```python
def valid_ip(s):
    parts = s.split('.')
    if len(parts) != 4:
        return False
    for p in parts:
        if p != '0' and p.lstrip('0') != p:
            return False
    for p in parts:
        if not p.isdigit():
            return False
        if not (0 <= int(p) <= 255):
            return False
    return True
```

### Approach 10 — state machine
```python
def valid_ip(s):
    parts = s.split('.')
    if len(parts) != 4:
        return False
    for p in parts:
        state = 'leading'
        val = 0
        for ch in p:
            if not ch.isdigit():
                return False
            if state == 'leading' and ch == '0' and len(p) > 1:
                return False
            state = 'digits'
            val = val * 10 + int(ch)
            if val > 255:
                return False
        if not p:
            return False
    return True
```

**Best:** `ipaddress.IPv4Address` for production; manual split+range for interview clarity.

---

## Problem 7 — Monotonic check

**Input:** `[1, 2, 2, 3]` or `[3, 2, 1]`
**Output:** True / True (monotonically non-decreasing or non-increasing)

### Approach 1 — two-pass comparison
```python
def monotonic(a):
    inc = True
    for i in range(len(a) - 1):
        if a[i] > a[i+1]:
            inc = False
            break
    if inc:
        return True
    dec = True
    for i in range(len(a) - 1):
        if a[i] < a[i+1]:
            dec = False
            break
    return dec
```

### Approach 2 — sorted + equal
```python
def monotonic(a):
    if a == sorted(a):
        return True
    if a == sorted(a, reverse=True):
        return True
    return False
```

### Approach 3 — single-pass flag
```python
def monotonic(a):
    inc = True
    dec = True
    for i in range(1, len(a)):
        if a[i] > a[i-1]:
            dec = False
        if a[i] < a[i-1]:
            inc = False
    return inc or dec
```

### Approach 4 — numpy diff
```python
import numpy as np
def monotonic(a):
    arr = np.array(a)
    d = np.diff(arr)
    if (d >= 0).all():
        return True
    if (d <= 0).all():
        return True
    return False
```

### Approach 5 — itertools pairwise
```python
from itertools import pairwise
def monotonic(a):
    inc = True
    dec = True
    for x, y in pairwise(a):
        if x > y:
            inc = False
        if x < y:
            dec = False
    return inc or dec
```

### Approach 6 — reduce
```python
from functools import reduce
def monotonic(a):
    pairs = list(zip(a, a[1:]))
    def check_inc(acc, t):
        x, y = t
        return acc and (x <= y)
    def check_dec(acc, t):
        x, y = t
        return acc and (x >= y)
    incr = reduce(check_inc, pairs, True)
    decr = reduce(check_dec, pairs, True)
    return incr or decr
```

### Approach 7 — pandas
```python
import pandas as pd
def monotonic(a):
    s = pd.Series(a)
    d = s.diff().dropna()
    if (d >= 0).all():
        return True
    if (d <= 0).all():
        return True
    return False
```

### Approach 8 — generator + any/all
```python
def monotonic(a):
    diffs = []
    for i in range(len(a) - 1):
        diffs.append(a[i+1] - a[i])
    all_non_neg = True
    all_non_pos = True
    for d in diffs:
        if d < 0:
            all_non_neg = False
        if d > 0:
            all_non_pos = False
    return all_non_neg or all_non_pos
```

### Approach 9 — recursive
```python
def monotonic(a):
    if len(a) <= 2:
        return True
    if a[0] <= a[1]:
        return all(a[i] <= a[i+1] for i in range(len(a)-1))
    if a[0] >= a[1]:
        return all(a[i] >= a[i+1] for i in range(len(a)-1))
    return False
```

### Approach 10 — set of directions
```python
def monotonic(a):
    if len(a) < 2:
        return True
    dirs = set()
    for i in range(len(a) - 1):
        if a[i+1] > a[i]:
            dirs.add(1)
        elif a[i+1] < a[i]:
            dirs.add(-1)
        else:
            dirs.add(0)
    if dirs <= {1, 0}:
        return True
    if dirs <= {-1, 0}:
        return True
    return False
```

**Best:** single-pass flag — O(n) time, O(1) space.

---

## Problem 8 — Words in one sentence but not the other (symmetric difference)

**Input:** s1 = "apple banana cherry", s2 = "banana date"
**Output:** `['apple', 'cherry', 'date']`

### Approach 1 — set symmetric_difference
```python
def sym_diff(s1, s2):
    a = set(s1.split())
    b = set(s2.split())
    diff = a ^ b
    out = []
    for w in diff:
        out.append(w)
    return out
```

### Approach 2 — Counter subtraction
```python
from collections import Counter
def sym_diff(s1, s2):
    a = Counter(s1.split())
    b = Counter(s2.split())
    only_a = list((a - b).elements())
    only_b = list((b - a).elements())
    return only_a + only_b
```

### Approach 3 — list comprehension
```python
def sym_diff(s1, s2):
    a = s1.split()
    b = s2.split()
    sa = set(a)
    sb = set(b)
    result = []
    for w in a:
        if w not in sb:
            result.append(w)
    for w in b:
        if w not in sa:
            result.append(w)
    return result
```

### Approach 4 — operator.xor
```python
import operator
def sym_diff(s1, s2):
    a = set(s1.split())
    b = set(s2.split())
    out = []
    for w in operator.xor(a, b):
        out.append(w)
    return out
```

### Approach 5 — dict counting
```python
def sym_diff(s1, s2):
    a = s1.split()
    b = s2.split()
    freq = {}
    for w in a + b:
        freq[w] = freq.get(w, 0) + 1
    result = []
    for w in a + b:
        if freq[w] == 1:
            result.append(w)
    return result
```

### Approach 6 — pandas
```python
import pandas as pd
def sym_diff(s1, s2):
    a = pd.Series(s1.split())
    b = pd.Series(s2.split())
    only_a = []
    for v in a[~a.isin(b)]:
        only_a.append(v)
    only_b = []
    for v in b[~b.isin(a)]:
        only_b.append(v)
    return only_a + only_b
```

### Approach 7 — reduce + set ops
```python
from functools import reduce
def sym_diff(s1, s2):
    a = s1.split()
    b = s2.split()
    final_set = reduce(lambda acc, w: acc ^ {w}, a + b, set())
    out = []
    for w in final_set:
        out.append(w)
    return out
```

### Approach 8 — sorted output via merge
```python
def sym_diff(s1, s2):
    a = set(s1.split())
    b = set(s2.split())
    diff = a ^ b
    out = []
    for w in sorted(diff):
        out.append(w)
    return out
```

### Approach 9 — generator with sentinel
```python
def sym_diff(s1, s2):
    a = s1.split()
    b = s2.split()
    sa = set(a)
    sb = set(b)
    for w in a:
        if w not in sb:
            yield w
    for w in b:
        if w not in sa:
            yield w
```

### Approach 10 — explicit two-filter concat
```python
def sym_diff(s1, s2):
    a = s1.split()
    b = s2.split()
    in_both = set(a) & set(b)
    combined = a + b
    result = []
    for w in combined:
        if w not in in_both:
            result.append(w)
    return result
```

**Best:** set symmetric_difference — O(n+m) and intent-matching.

---

## Problem 9 — Count pair-membership per person (from 2D list of pairs)

**Input:** `[[2,3],[3,4],[5]]` (each sublist = one group; count how many groups each person appears in).
**Output:** `{2: 1, 3: 2, 4: 1, 5: 1}`

Note: differs from Problem 1, which counts unique partners. Here we count group membership.

### Approach 1 — Counter on flattened
```python
from collections import Counter
from itertools import chain
def neighbors(graph):
    all_nodes = list(chain.from_iterable(graph))
    c = Counter(all_nodes)
    result = {}
    for k, v in c.items():
        result[k] = v
    return result
```

### Approach 2 — defaultdict
```python
from collections import defaultdict
def neighbors(graph):
    d = defaultdict(int)
    for edge in graph:
        for n in edge:
            d[n] += 1
    result = {}
    for k, v in d.items():
        result[k] = v
    return result
```

### Approach 3 — list count
```python
def neighbors(graph):
    flat = []
    for edge in graph:
        for n in edge:
            flat.append(n)
    unique = set(flat)
    result = {}
    for n in unique:
        result[n] = flat.count(n)
    return result
```

### Approach 4 — pandas
```python
import pandas as pd
def neighbors(graph):
    all_nodes = []
    for edge in graph:
        for n in edge:
            all_nodes.append(n)
    counts = pd.Series(all_nodes).value_counts()
    result = {}
    for k, v in counts.items():
        result[k] = int(v)
    return result
```

### Approach 5 — numpy bincount
```python
import numpy as np
def neighbors(graph):
    flat_list = []
    for edge in graph:
        for n in edge:
            flat_list.append(n)
    arr = np.array(flat_list)
    unique, counts = np.unique(arr, return_counts=True)
    result = {}
    for i in range(len(unique)):
        result[int(unique[i])] = int(counts[i])
    return result
```

### Approach 6 — reduce
```python
from functools import reduce
def neighbors(graph):
    def step(d, edge):
        for n in edge:
            d[n] = d.get(n, 0) + 1
        return d
    return reduce(step, graph, {})
```

### Approach 7 — dict comprehension
```python
def neighbors(graph):
    flat = []
    for edge in graph:
        for n in edge:
            flat.append(n)
    seen = []
    for n in flat:
        if n not in seen:
            seen.append(n)
    result = {}
    for n in seen:
        result[n] = flat.count(n)
    return result
```

### Approach 8 — Counter with explicit init
```python
from collections import Counter
def neighbors(graph):
    c = Counter()
    for edge in graph:
        c.update(edge)
    result = {}
    for k, v in c.items():
        result[k] = v
    return result
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

**Input:** `{'a': 10, 'b': 20, 'c': 30, 'd': 20}`, n=2
**Output:** `'b'` (second highest value is 20, smallest key with that value)

### Approach 1 — sort + iterate
```python
def nth_key(d, n):
    items = sorted(d.items(), key=lambda kv: kv[1], reverse=True)
    unique_vals = sorted(set(d.values()), reverse=True)
    target = unique_vals[n-1]
    for k, v in items:
        if v == target:
            return k
    return None
```

### Approach 2 — heapq.nlargest
```python
import heapq
def nth_key(d, n):
    unique = sorted(set(d.values()), reverse=True)
    target = unique[n-1]
    candidates = []
    for k, v in d.items():
        if v == target:
            candidates.append(k)
    candidates.sort()
    return candidates[0]
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
            if len(seen) == n:
                return k
    return None
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
    keys = list(d.keys())
    vals = np.array(list(d.values()))
    order = np.argsort(-vals, kind='stable')
    return keys[order[n-1]]
```

### Approach 7 — manual scan
```python
def nth_key(d, n):
    pairs = []
    for k, v in d.items():
        pairs.append((v, k))
    pairs.sort(reverse=True)
    seen_vals = []
    target_v = None
    for v, k in pairs:
        if not seen_vals or seen_vals[-1] != v:
            seen_vals.append(v)
        if len(seen_vals) == n:
            target_v = v
            break
    candidates = []
    for v, k in pairs:
        if v == target_v:
            candidates.append(k)
    candidates.sort()
    return candidates[0]
```

### Approach 8 — dict inversion + sorted
```python
def nth_key(d, n):
    inv = {}
    for k, v in d.items():
        if v not in inv:
            inv[v] = []
        inv[v].append(k)
    for v in sorted(inv.keys(), reverse=True):
        if n == 1:
            candidates = sorted(inv[v])
            return candidates[0]
        n -= 1
    return None
```

### Approach 9 — reduce
```python
from functools import reduce
def nth_key(d, n):
    unique_vals = sorted(set(d.values()), reverse=True)
    target = unique_vals[n-1]
    candidates = []
    for k, v in d.items():
        if v == target:
            candidates.append(k)
    candidates.sort()
    return reduce(lambda a, b: a if a < b else b, candidates)
```

### Approach 10 — sorted zip trick
```python
def nth_key(d, n):
    keys = list(d.keys())
    vals = list(d.values())
    order = sorted(range(len(vals)), key=lambda i: (-vals[i], keys[i]))
    return keys[order[n-1]]
```

**Best:** sort once with tie-breaker `(value desc, key asc)` — single pass.

---

## Problem 11 — Flatten nested dictionary

**Input:** `{'a': {'b': 1, 'c': {'d': 2}}}`
**Output:** `{'a.b': 1, 'a.c.d': 2}`

### Approach 1 — recursive
```python
def flatten(d, parent_key='', sep='.'):
    items = {}
    for k, v in d.items():
        if parent_key:
            key = f'{parent_key}{sep}{k}'
        else:
            key = k
        if isinstance(v, dict):
            sub = flatten(v, key, sep=sep)
            items.update(sub)
        else:
            items[key] = v
    return items
```

### Approach 2 — stack/iterative
```python
def flatten(d, sep='.'):
    items = {}
    stack = [((), d)]
    while stack:
        prefix, obj = stack.pop()
        for k, v in obj.items():
            key = prefix + (k,)
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
        if parent_key:
            key = f'{parent_key}{sep}{k}'
        else:
            key = k
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
            sub = flatten(v, sep=sep)
            merged = dict(acc)
            for sk, sv in sub.items():
                merged[f'{k}{sep}{sk}'] = sv
            return merged
        merged = dict(acc)
        merged[k] = v
        return merged
    return reduce(step, d.items(), {})
```

### Approach 5 — BFS with queue
```python
from collections import deque
def flatten(d, sep='.'):
    out = {}
    q = deque([((), d)])
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
def flatten(d, sep='.'):
    flat = {}
    def walk(prefix, obj):
        for k, v in obj.items():
            if prefix:
                key = f'{prefix}{sep}{k}'
            else:
                key = k
            if isinstance(v, dict):
                walk(key, v)
            else:
                flat[key] = v
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
            if path:
                new_path = f'{path}{sep}{k}'
            else:
                new_path = k
            if isinstance(v, dict):
                helper(v, new_path)
            else:
                out[new_path] = v
    helper(d, '')
    return out
```

### Approach 9 — operator + comprehension
```python
def _iter_paths(d, prefix=()):
    for k, v in d.items():
        key = prefix + (k,)
        if isinstance(v, dict):
            yield from _iter_paths(v, key)
        else:
            yield key, v

def flatten(d, sep='.'):
    result = {}
    for k_tuple, v in _iter_paths(d):
        result[sep.join(k_tuple)] = v
    return result
```

### Approach 10 — class-based with __missing__
```python
class FlatDict(dict):
    def __missing__(self, key):
        return {}

def flatten(d, sep='.'):
    out = {}
    def helper(prefix, obj):
        for k, v in obj.items():
            if prefix:
                new_key = f'{prefix}{sep}{k}'
            else:
                new_key = k
            if isinstance(v, dict):
                helper(new_key, v)
            else:
                out[new_key] = v
    helper('', d)
    return out
```

**Best:** recursive generator — handles arbitrary depth cleanly.

---

## Problem 12 — Directed graph: in-degree and out-degree per node

**Input:** `[[2,3],[3,4],[5,3]]` (each pair = directed edge from A to B).
**Output:** `{'in': {3: 2, 4: 1}, 'out': {2: 1, 3: 1, 5: 1}}`

Differentiates from Problem 1 by being **directed** and returning two separate counts.

### Approach 1 — two Counters
```python
from collections import Counter
def degrees(pairs):
    srcs = []
    dsts = []
    for a, b in pairs:
        srcs.append(a)
        dsts.append(b)
    out_d = dict(Counter(srcs))
    in_d = dict(Counter(dsts))
    return {'in': in_d, 'out': out_d}
```

### Approach 2 — defaultdict
```python
from collections import defaultdict
def degrees(pairs):
    in_d = defaultdict(int)
    out_d = defaultdict(int)
    for a, b in pairs:
        out_d[a] += 1
        in_d[b] += 1
    return {'in': dict(in_d), 'out': dict(out_d)}
```

### Approach 3 — dict.get loop
```python
def degrees(pairs):
    in_d = {}
    out_d = {}
    for a, b in pairs:
        out_d[a] = out_d.get(a, 0) + 1
        in_d[b] = in_d.get(b, 0) + 1
    return {'in': in_d, 'out': out_d}
```

### Approach 4 — pandas groupby
```python
import pandas as pd
def degrees(pairs):
    srcs = []
    dsts = []
    for a, b in pairs:
        srcs.append(a)
        dsts.append(b)
    df = pd.DataFrame({'src': srcs, 'dst': dsts})
    in_counts = df['dst'].value_counts()
    out_counts = df['src'].value_counts()
    in_d = {}
    for k, v in in_counts.items():
        in_d[k] = int(v)
    out_d = {}
    for k, v in out_counts.items():
        out_d[k] = int(v)
    return {'in': in_d, 'out': out_d}
```

### Approach 5 — numpy bincount on src and dst
```python
import numpy as np
def degrees(pairs):
    srcs = []
    dsts = []
    for a, b in pairs:
        srcs.append(a)
        dsts.append(b)
    src_arr = np.array(srcs)
    dst_arr = np.array(dsts)
    out_u, out_c = np.unique(src_arr, return_counts=True)
    in_u, in_c = np.unique(dst_arr, return_counts=True)
    out_d = {}
    for i in range(len(out_u)):
        out_d[int(out_u[i])] = int(out_c[i])
    in_d = {}
    for i in range(len(in_u)):
        in_d[int(in_u[i])] = int(in_c[i])
    return {'in': in_d, 'out': out_d}
```

### Approach 6 — reduce
```python
from functools import reduce
def degrees(pairs):
    def step(acc, edge):
        a, b = edge
        acc['out'][a] = acc['out'].get(a, 0) + 1
        acc['in'][b] = acc['in'].get(b, 0) + 1
        return acc
    return reduce(step, pairs, {'in': {}, 'out': {}})
```

### Approach 7 — list comprehensions + Counter
```python
from collections import Counter
def degrees(pairs):
    srcs = [a for a, _ in pairs]
    dsts = [b for _, b in pairs]
    return {'in': dict(Counter(dsts)), 'out': dict(Counter(srcs))}
```

### Approach 8 — single dict of dicts
```python
def degrees(pairs):
    d = {}
    for a, b in pairs:
        if a not in d:
            d[a] = {'in': 0, 'out': 0}
        d[a]['out'] += 1
        if b not in d:
            d[b] = {'in': 0, 'out': 0}
        d[b]['in'] += 1
    return d
```

### Approach 9 — zip + Counter
```python
from collections import Counter
def degrees(pairs):
    if pairs:
        srcs, dsts = zip(*pairs)
    else:
        srcs, dsts = [], []
    return {'in': dict(Counter(dsts)), 'out': dict(Counter(srcs))}
```

### Approach 10 — pandas melt
```python
import pandas as pd
def degrees(pairs):
    srcs = []
    dsts = []
    for a, b in pairs:
        srcs.append(a)
        dsts.append(b)
    df = pd.DataFrame({'src': srcs, 'dst': dsts})
    out_counts = df['src'].value_counts()
    out_d = {}
    for k, v in out_counts.items():
        out_d[k] = int(v)
    in_counts = df['dst'].value_counts()
    in_d = {}
    for k, v in in_counts.items():
        in_d[k] = int(v)
    all_keys = set(out_d.keys()) | set(in_d.keys())
    result = {}
    for k in all_keys:
        result[k] = {'in': in_d.get(k, 0), 'out': out_d.get(k, 0)}
    return result
```

**Best:** two Counters (Approach 1) or defaultdict (Approach 2) — clean and idiomatic.
