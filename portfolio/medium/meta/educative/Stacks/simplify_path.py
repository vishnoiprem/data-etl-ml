"""
Simplify Path
Medium | 30 min

Given a string path (Unix-style absolute path), simplify it by:
1. Multiple slashes // -> single /
2. "." means current directory (ignore)
3. ".." means parent directory (go up - pop from stack)
4. Other names are directory/file names (push to stack)

Return the canonical path.

Examples:
    "/home/"                -> "/home"
    "/../"                  -> "/"
    "/home//foo/"           -> "/home/foo"
    "/a/./b/../../c/"       -> "/c"
    "/a/../../b"            -> "/b"
    "/..."                  -> "/..."

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/simplify-path

Constraints:
- 1 <= path.length <= 3000
- path consists of English letters, digits, '.', '/', '_'
- path is valid (always starts with '/')
"""


# =============================================================================
# WAY 1: Stack-based canonical path (BEST - Memorize!)
# =============================================================================
def simplify_path_1(path):
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


# =============================================================================
# WAY 2: Same with manual split
# =============================================================================
def simplify_path_2(path):
    stack = []
    i = 0
    n = len(path)
    while i < n:
        # Skip slashes
        while i < n and path[i] == '/':
            i += 1
        # Read part
        start = i
        while i < n and path[i] != '/':
            i += 1
        part = path[start:i]
        if part == '' or part == '.':
            continue
        elif part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 3: Split, process, reconstruct
# =============================================================================
def simplify_path_3(path):
    parts = path.split('/')
    stack = []
    for part in parts:
        if part == '' or part == '.':
            continue
        if part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 4: Using deque
# =============================================================================
def simplify_path_4(path):
    from collections import deque
    stack = deque()
    for part in path.split('/'):
        if part == '' or part == '.':
            continue
        elif part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 5: Reversed processing
# =============================================================================
def simplify_path_5(path):
    parts = path.split('/')
    result = []
    for part in parts:
        if part == '..':
            if result:
                result.pop()
        elif part == '' or part == '.':
            continue
        else:
            result.append(part)
    return '/' + '/'.join(result)


# =============================================================================
# WAY 6: Filter then process
# =============================================================================
def simplify_path_6(path):
    # First pass: filter out '.' and empty
    parts = [p for p in path.split('/') if p and p != '.']
    stack = []
    for p in parts:
        if p == '..':
            if stack:
                stack.pop()
        else:
            stack.append(p)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 7: With counter tracking
# =============================================================================
def simplify_path_7(path):
    stack = []
    up_count = 0  # number of .. to apply
    parts = path.split('/')
    # Process from end to start to handle .. effectively
    for part in reversed(parts):
        if part == '' or part == '.':
            continue
        elif part == '..':
            up_count += 1
        elif up_count > 0:
            up_count -= 1
        else:
            stack.append(part)
    return '/' + '/'.join(reversed(stack))


# =============================================================================
# WAY 8: Using list comprehension for join
# =============================================================================
def simplify_path_8(path):
    stack = []
    for part in path.split('/'):
        if part == '..':
            if stack:
                stack.pop()
        elif part and part != '.':
            stack.append(part)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 9: Iterative with index
# =============================================================================
def simplify_path_9(path):
    stack = []
    i = 0
    n = len(path)
    while i < n:
        # Skip leading slashes
        if path[i] == '/':
            i += 1
            continue
        # Find next slash
        j = i
        while j < n and path[j] != '/':
            j += 1
        part = path[i:j]
        if part == '.':
            pass
        elif part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
        i = j
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 10: Using re.split
# =============================================================================
def simplify_path_10(path):
    import re
    parts = re.split('/', path)
    stack = []
    for part in parts:
        if part == '' or part == '.':
            continue
        elif part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 11: Functional style with filter
# =============================================================================
def simplify_path_11(path):
    def process(parts):
        result = []
        for p in parts:
            if p == '' or p == '.':
                continue
            if p == '..':
                if result:
                    result.pop()
            else:
                result.append(p)
        return result
    stack = process(path.split('/'))
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 12: With reduce
# =============================================================================
def simplify_path_12(path):
    from functools import reduce
    def reducer(stack, part):
        if part == '' or part == '.':
            return stack
        if part == '..':
            return stack[:-1] if stack else stack
        return stack + [part]
    stack = reduce(reducer, path.split('/'), [])
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 13: Using generators
# =============================================================================
def simplify_path_13(path):
    def parts():
        for p in path.split('/'):
            if p and p != '.':
                yield p

    stack = []
    for p in parts():
        if p == '..':
            if stack:
                stack.pop()
        else:
            stack.append(p)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 14: Brute force with string operations
# =============================================================================
def simplify_path_14(path):
    """Brute force - regex-based split and process."""
    import re
    # Split by / but keep the structure
    parts = re.findall(r'/|[^/]+', path)
    stack = []
    i = 0
    while i < len(parts):
        p = parts[i]
        if p == '/':
            i += 1
            # Collect non-slash chars
            name = ''
            while i < len(parts) and parts[i] != '/':
                name += parts[i]
                i += 1
            if name == '' or name == '.':
                continue
            elif name == '..':
                if stack:
                    stack.pop()
            else:
                stack.append(name)
        else:
            i += 1
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 15: Two-pass split
# =============================================================================
def simplify_path_15(path):
    parts = path.split('/')
    stack = []
    for p in parts:
        if not p or p == '.':
            continue
        if p == '..':
            if stack:
                stack.pop()
            continue
        stack.append(p)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 16: With while loop and re.split
# =============================================================================
def simplify_path_16(path):
    import re
    tokens = re.findall(r'[^/]+', path)  # any non-slash sequence
    stack = []
    for token in tokens:
        if token == '.':
            continue
        elif token == '..':
            if stack:
                stack.pop()
        else:
            stack.append(token)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 17: Most concise
# =============================================================================
def simplify_path_17(path):
    stack = []
    for p in path.split('/'):
        if p == '..':
            if stack: stack.pop()
        elif p and p != '.':
            stack.append(p)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 18: One-liner with list comprehension
# =============================================================================
def simplify_path_18(path):
    stack = []
    for p in path.split('/'):
        if p == '..':
            if stack: stack.pop()
        elif p and p != '.':
            stack.append(p)
    return '/' + '/'.join(stack)


# =============================================================================
# WAY 19: Class-based
# =============================================================================
class PathSimplifier:
    def __init__(self, path):
        self.path = path
        self.stack = []

    def simplify(self):
        for p in self.path.split('/'):
            if p == '' or p == '.':
                continue
            if p == '..':
                if self.stack:
                    self.stack.pop()
            else:
                self.stack.append(p)
        return '/' + '/'.join(self.stack)


def simplify_path_19(path):
    return PathSimplifier(path).simplify()


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def simplify_path_20(path):
    stack = []
    for p in path.split('/'):
        if p == '..':
            if stack:
                stack.pop()
        elif p and p != '.':
            stack.append(p)
    return '/' + '/'.join(stack)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to simplify a Unix-style absolute path:
- '//' collapses to '/'
- '.' means current directory (skip)
- '..' means parent (pop from stack)
- Other names are directory/file names (push to stack)"

Key Insight:
"Use a STACK! Split the path by '/', then process each part:
- '' or '.': skip
- '..': pop (if stack non-empty)
- Otherwise: push the name

Final result is '/' + '/'.join(stack)."

Algorithm:
"1. Split path by '/'
2. For each part:
   - If empty or '.': continue
   - If '..': pop stack if non-empty
   - Else: push to stack
3. Return '/' + '/'.join(stack)"

Why this works:
"Splitting by '/' handles multiple slashes naturally (empty parts skipped).
The stack represents the current directory path. '..' pops the last directory.
Names are added to the path. At the end, we have the canonical path."

Edge cases:
- All '..': stack empties, result is '/'
- Path with '.': '.' is skipped, others proceed
- No slashes: just the name
- Empty result: '/'
- '..' at root: ignored (can't go above root)
- Triple dots '...': it's a directory NAME, not '..' or '.'

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Stack     | O(n)   | O(n)   |
| String    | O(n^2) | O(n)   |
+-----------+--------+--------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack", simplify_path_1),
        ("Way 2: Manual split", simplify_path_2),
        ("Way 3: Split + process", simplify_path_3),
        ("Way 4: Deque", simplify_path_4),
        ("Way 5: Reversed", simplify_path_5),
        ("Way 6: Filter then process", simplify_path_6),
        ("Way 7: Counter tracking", simplify_path_7),
        ("Way 8: List comp join", simplify_path_8),
        ("Way 9: Iterative with index", simplify_path_9),
        ("Way 10: re.split", simplify_path_10),
        ("Way 11: Functional filter", simplify_path_11),
        ("Way 12: Reduce", simplify_path_12),
        ("Way 13: Generators", simplify_path_13),
        ("Way 14: Brute force string", simplify_path_14),
        ("Way 15: Two-pass split", simplify_path_15),
        ("Way 16: re.findall", simplify_path_16),
        ("Way 17: Most concise", simplify_path_17),
        ("Way 18: One-liner", simplify_path_18),
        ("Way 19: Class-based", simplify_path_19),
        ("Way 20: Final cleanest", simplify_path_20),
    ]

    test_cases = [
        ("/home/", "/home"),
        ("/../", "/"),
        ("/home//foo/", "/home/foo"),
        ("/a/./b/../../c/", "/c"),
        ("/a/../../b", "/b"),
        ("/...", "/..."),
        ("/", "/"),
        ("/a/b/c", "/a/b/c"),
        ("/a/b/c/", "/a/b/c"),
        ("/a/./b/./c/./d/", "/a/b/c/d"),
        ("/a/b/../../..", "/"),
        ("/././.", "/"),
        ("/foo/../bar/../../baz", "/baz"),
    ]

    print("=" * 70)
    print("SIMPLIFY PATH - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/simplify-path")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for path, expected in test_cases:
            try:
                result = func(path)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: '{path}' -> '{result}' (expected '{expected}')")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on '{path}' - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
