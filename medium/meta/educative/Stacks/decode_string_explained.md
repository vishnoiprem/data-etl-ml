# Decode String - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/decode-string

## The Problem
```
Given an encoded string, return its decoded version.
Encoding rule: k[encoded_string] = repeat encoded_string k times.

Examples:
    "3[a]2[bc]"        -> "aaabcbc"
    "3[a2[c]]"         -> "accaccacc"
    "2[abc]3[cd]ef"    -> "abcabccdcdcdef"

Constraints:
- 1 <= s.length <= 30
- 1 <= k <= 100
- s consists of lowercase English letters, digits, and square brackets
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "3[a2[c]]"
- 3[...] means repeat inside 3 times
- inside: "a2[c]" = "a" + "cc" = "acc"
- Final: "acc" * 3 = "accaccacc"

Tree:
  3[...]
    a
    2[c]
      c
```

### Step 2: The Trick
> "TWO STACKS:
> - count_stack: stores repeat counts
> - string_stack: stores strings built BEFORE current bracket
> - When '[': push current state and reset
> - When ']': pop and combine: prev + (current * count)"

### Step 3: Why Two Stacks?
> "When we open '[', we need to save the OUTER context.
> When we close ']', we combine inner with outer.
> Two parallel stacks track counts and strings at each nesting level."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to decode a string with nested k[encoded_string] patterns. The trick is using two stacks to track the contexts at each nesting level."

**Key Insight:**
> "When I see '[', I'm entering a NEW context. I save my current string and count on stacks, then start fresh inside. When I see ']', I'm closing the current context. I take what I built, multiply by the count, and prepend the saved outer string."

**Algorithm:**
> "1. count_stack = [], string_stack = [], current = '', num = 0
> 2. For each char:
>    - Digit: build multi-digit number
>    - '[': push num and current to stacks, reset both
>    - ']': pop count and prev_string, current = prev + current * count
>    - Letter: append to current
> 3. Return current"

**Why this works:**
> "Each '[' opens a new nested context. We push the OUTER state (count + string) onto stacks. Each ']' closes a context - we combine: prev_string + (current_inner * count). The stacks perfectly model the LIFO nesting."

**Edge cases:**
- Multi-digit numbers: "10[a]" -> "aaaaaaaaaa"
- Nested: "3[a2[c]]" -> "accaccacc"
- Empty input: "" -> ""
- Single char: "a" -> "a"

---

## The 20 Implementations (Simple to Complex)

### Way 1: Two Stacks (BEST - Memorize!)
```python
def decodeString(s):
    count_stack = []
    string_stack = []
    current_string = ""
    current_num = 0

    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            count_stack.append(current_num)
            string_stack.append(current_string)
            current_num = 0
            current_string = ""
        elif char == ']':
            repeat_count = count_stack.pop()
            prev_string = string_stack.pop()
            current_string = prev_string + current_string * repeat_count
        else:
            current_string += char

    return current_string
```

### Way 2: Single Tuple Stack
```python
def decodeString(s):
    stack = []
    current_string = ""
    current_num = 0

    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            stack.append((current_num, current_string))
            current_num = 0
            current_string = ""
        elif char == ']':
            count, prev = stack.pop()
            current_string = prev + current_string * count
        else:
            current_string += char

    return current_string
```

### Way 3: Recursive with Index
```python
def decodeString(s):
    idx = [0]

    def parse():
        result = ""
        num = 0
        while idx[0] < len(s):
            ch = s[idx[0]]
            if ch.isdigit():
                num = num * 10 + int(ch)
                idx[0] += 1
            elif ch == '[':
                idx[0] += 1  # skip '['
                inner = parse()
                result += inner * num
                num = 0
            elif ch == ']':
                idx[0] += 1  # skip ']'
                return result
            else:
                result += ch
                idx[0] += 1
        return result

    return parse()
```

### Way 4-10: More variations
- Way 4: deque for stacks
- Way 5: Stack of tuples (multiplier_so_far, accumulated)
- Way 6: Recursive with mutable index list
- Way 7: Decoder class
- Way 8: reduce-based
- Way 9: Compact tuple
- Way 10: Index pointer recursion

### Way 11-15: Specialized
- Way 11: Nested stack with explicit count
- Way 12: Two-pass bracket matching
- Way 13: Most compact (Way 1 minimal)
- Way 14: Explicit state
- Way 15: reduce with 4-tuple state

### Way 16-20: Compact variations
- Way 16: deque + tracking
- Way 17: Recursive global idx
- Way 18: Most elegant
- Way 19: Nested list stack
- Way 20: Helper variables

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Most elegant     | 2 stacks    | Standard     |
| Functional       | reduce      | No loops     |
| Recursive        | Parse fn    | Math-like    |
| Most compact     | Way 13      | Fewest lines |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| 2 stacks | O(n*K) | O(n) |
| Recursive | O(n*K) | O(n) |
| reduce | O(n*K) | O(n) |

where K = max repetition count, n = input length.

---

## Walkthrough Example

```
s = "3[a2[c]]"

i=0, '3': current_num=3
i=1, '[': push count=3, push string=""
        stack: counts=[3], strings=[""]
        reset current_num=0, current_string=""
i=2, 'a': current_string="a"
i=3, '2': current_num=2
i=4, '[': push count=2, push string="a"
        stack: counts=[3,2], strings=["", "a"]
        reset current_num=0, current_string=""
i=5, 'c': current_string="c"
i=6, ']': pop count=2, pop prev="a"
        current_string = "a" + "c" * 2 = "acc"
        stack: counts=[3], strings=[""]
i=7, ']': pop count=3, pop prev=""
        current_string = "" + "acc" * 3 = "accaccacc"
        stack: empty

Final: "accaccacc" ✓
```

```
s = "2[abc]3[cd]ef"

After parsing 2[abc]:
  stack=[], current="abcabc"

Then 3[cd]:
  push "abcabc" and 3, reset
  current="cdcdcd"
  pop: current = "abcabc" + "cdcdcd" * 3 ... wait
  
Let me re-trace. After 2[abc], current="abcabc", stack=[].
Then '3' makes current_num=3.
Then '[' pushes current_num=3 and current_string="abcabc" onto stacks.
Then "cd" makes current="cd".
Then ']': pop count=3, pop prev="abcabc"
  current = "abcabc" + "cd" * 3 = "abcabccdcdcd"
Then "ef": current = "abcabccdcdcdef" ✓
```

## Best Answer to Memorize

```python
def decodeString(s):
    count_stack = []
    string_stack = []
    current_string = ""
    current_num = 0

    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            count_stack.append(current_num)
            string_stack.append(current_string)
            current_num = 0
            current_string = ""
        elif char == ']':
            repeat_count = count_stack.pop()
            prev_string = string_stack.pop()
            current_string = prev_string + current_string * repeat_count
        else:
            current_string += char

    return current_string
```

**15 lines. O(n*K) time. Clean. Interview-ready!**

## Key Insights

### Why Two Stacks?
> "When we open a bracket, we need to remember TWO things:
> 1. The count for this bracket (for ']' to use)
> 2. The string built BEFORE this bracket (to prepend when ']' closes)
> Two parallel stacks store both at each nesting level."

### Why Reset on '['?
> "Inside '[', we're building a NEW string context.
> The OUTER string is saved; inner starts fresh."

### Why prev + current * count?
> "When we close a bracket, we have:
> - Inner string (what we built inside)
> - Count (how many times to repeat)
> - Outer string (what was built before)
> We combine: outer + (inner * count)"

## Test Cases

| s | Expected | Why |
|---|----------|-----|
| 3[a]2[bc] | aaabcbc | Two groups |
| 3[a2[c]] | accaccacc | Nested |
| 2[abc]3[cd]ef | abcabccdcdcdef | Multiple groups + suffix |
| abc | abc | No encoding |
| 10[a] | aaaaaaaaaa | Multi-digit |
| 100[leetcode] | leetcode*100 | Large count |
| 2[2[b]] | bbbb | Nested with multi-digit |

## Common Pitfalls

1. **Multi-digit numbers**: Don't just use `int(char)` - build up multi-digit
2. **Forgetting to reset on '['**: Inner contaminates outer
3. **Wrong combine order**: Must be `prev + inner * count`, not the other way
4. **Empty brackets**: "3[]" gives "" (problem says valid input but be defensive)

## Why This Problem Matters

> "Classic nested structure problem. Tests:
> 1. Stack understanding (LIFO for nested contexts)
> 2. Multi-digit number parsing
> 3. State management (multiple variables)
> 4. Edge case handling (multi-digit, nested, empty)
> 5. Clean code organization"
