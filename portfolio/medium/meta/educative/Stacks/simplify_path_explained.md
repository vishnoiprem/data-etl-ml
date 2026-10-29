# Simplify Path - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/simplify-path

## The Problem
```
Given an ABSOLUTE Unix-style path, simplify it (return the CANONICAL path).

Rules:
- Multiple slashes // -> single /
- "." means current directory (ignore)
- ".." means parent directory (pop from stack)
- Other names are directory/file names (push to stack)
- ".." at root is ignored

Examples:
    "/home/"           -> "/home"
    "/../"             -> "/"
    "/home//foo/"      -> "/home/foo"
    "/a/./b/../../c/"  -> "/c"
    "/..."             -> "/..."  (three dots is a NAME)
    "/foo/../bar/.."   -> "/"

Constraints:
- 1 <= path.length <= 3000
- path is valid (always starts with '/')
- Consists of English letters, digits, '.', '/', '_'
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Path = "/a/./b/../../c/"
Split by '/': ["", "a", ".", "b", "..", "..", "c", ""]

Walk through:
- "": skip
- "a": push. stack=["a"]
- ".": skip (current dir)
- "b": push. stack=["a", "b"]
- "..": pop. stack=["a"]
- "..": pop. stack=[]
- "c": push. stack=["c"]
- "": skip

Final: "/" + "c" = "/c" ✓
```

### Step 2: The Trick
> "Split the path by '/'. The empty parts and '.' parts are SKIP.
> '..' POPS the stack. Anything else PUSHES.
> Final path = '/' + '/'.join(stack)."

### Step 3: Why Stack?
> "The stack represents the current directory hierarchy. Going up
> means popping the last directory. Going deeper means pushing.
> Multiple slashes create empty parts which are skipped.
> Three dots ('...') is a directory NAME (not special)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to simplify a Unix-style absolute path:
> - '//' collapses to '/'
> - '.' is current directory (skip)
> - '..' is parent directory (pop)
> - Other names are directory/file names (push)"

**Key Insight:**
> "Use a STACK! Split by '/' and process each part:
> - '' or '.': skip
> - '..': pop stack if non-empty
> - Otherwise: push to stack
> Final: '/' + '/'.join(stack)"

**Algorithm:**
> "1. parts = path.split('/')
> 2. For each part:
>    - If '' or '.': skip
>    - If '..': pop stack if non-empty
>    - Else: push to stack
> 3. Return '/' + '/'.join(stack)"

**Why this works:**
> "Splitting handles multiple slashes (empty parts skipped).
> The stack represents the current path. '..' pops the last directory.
> Three dots '...' is just a name - it doesn't match '..' (only 2 chars)."

**Edge cases:**
- ".." at root: can't go higher, ignored (stack stays empty)
- Multiple slashes: "//" splits to ['', '', 'a'] - empty parts skipped
- Three dots "...": directory name, not '..'
- All "..": result is "/"
- No directory names: result is "/"

**Complexity:**
- Time: O(n) where n is length of path
- Space: O(n) for the stack

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack-based (BEST - Memorize!)
```python
def simplifyPath(path):
    stack = []
    for part in path.split('/'):
        if part == '' or part == '.':
            continue
        elif part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)
```

### Way 2-5: Variations
- Way 2: Manual split with index
- Way 3: Same as Way 1, different naming
- Way 4: Using deque
- Way 5: Process from end with counter

### Way 6: Filter then process

### Way 7: Reverse processing with up_count
```python
for part in reversed(parts):
    if part == '..':
        up_count += 1
    elif up_count > 0:
        up_count -= 1
    else:
        stack.append(part)
```

### Way 8-13: Various implementations
- Way 8: List comp join
- Way 9: Iterative with index
- Way 10: re.split
- Way 11: Functional filter style
- Way 12: Using reduce
- Way 13: Generators

### Way 14: Brute force regex-based

### Way 15-16: Variations
- Way 15: Two-pass split
- Way 16: re.findall

### Way 17-18: Most concise
- Way 17: 4-line condensed version
- Way 18: One-liner (hard to do correctly)

### Way 19: Class-based

### Way 20: Final cleanest (same as Way 1)

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Most efficient   | Way 1    | Clean stack  |
| Educational      | Way 7    | Reverse logic|
| Functional       | Way 12   | reduce()     |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack (Way 1) | O(n) | O(n) |
| Reverse (Way 7) | O(n) | O(n) |
| Brute force | O(n²) | O(n) |

---

## Walkthrough Example

```
path = "/a/./b/../../c/"

parts = ['a', '.', 'b', '..', '..', 'c', '']  (split by '/', empty first removed)

Process:
- 'a': push. stack=[a]
- '.': skip. stack=[a]
- 'b': push. stack=[a, b]
- '..': pop. stack=[a]
- '..': pop. stack=[]
- 'c': push. stack=[c]
- '': skip.

Return '/' + '/'.join([c]) = '/c' ✓

path = "/foo/../bar/../../baz"

parts = ['foo', '..', 'bar', '..', '..', 'baz']

Process:
- 'foo': push. [foo]
- '..': pop. []
- 'bar': push. [bar]
- '..': pop. []
- '..': skip (no pop, empty stack). []
- 'baz': push. [baz]

Return '/' + '/baz' = '/baz' ✓
```

## Best Answer to Memorize

```python
def simplifyPath(path):
    stack = []
    for part in path.split('/'):
        if part == '' or part == '.':
            continue
        elif part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)
```

**8 lines. O(n) time. Clean. Interview-ready!**

---

## Key Insights

### Why split by '/'?
> "Multiple slashes create empty parts which we skip. The 'split'
> automatically handles '//', '///', etc."

### Why is '..' at root ignored?
> "We can only pop if the stack is non-empty. At root, the stack is
> empty, so '..' does nothing - we can't go above root."

### What about '...'?
> "Three dots is a directory NAME, not the parent operator (which is
> only '..' with two chars). String equality distinguishes them."

### Why '/' + '/'.join(stack)?
> "The result must always start with '/' (it's an absolute path).
> Stack items joined with '/' give the rest of the path."

---

## Test Cases

| path | Result | Why |
|------|--------|-----|
| /home/ | /home | Trailing / removed |
| /../ | / | .. at root |
| /home//foo/ | /home/foo | // collapsed |
| /a/./b/../../c/ | /c | Multiple ups |
| /... | /... | Three dots is name |
| / | / | Already canonical |
| /a/b/c/ | /a/b/c | Trailing / |
| /./ | / | . is current dir |
| /a/b/../../.. | / | Past root |

## Common Pitfalls

1. **Three dots vs two dots**: "..." is a NAME, not the parent op.
2. **'..' at root**: can't go above, ignored gracefully.
3. **Multiple slashes**: must collapse correctly.
4. **Empty path parts**: from '//' are skipped.
5. **Trailing slash**: removed (no empty trailing dir).

## Why This Problem Matters

> "Tests:
> 1. Stack for hierarchical navigation (CRITICAL)
> 2. String parsing with multiple special tokens
> 3. Edge case: multiple slashes, leading/trailing slashes
> 4. Pattern similar to: expression evaluation, nested structures
> 5. Important: distinguish '..' from '...' (2 vs 3 dots)"
