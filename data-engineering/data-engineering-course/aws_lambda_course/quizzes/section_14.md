# Quiz — Section 14: Python Basics Appendix (L78–L81)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 14 — Python Basics Appendix
> **Total questions:** 10
> **Passing score:** 8 / 10

This quiz covers the Python beginner material in L78–L81: `print`,
variables, f-strings, `input`, the four basic data types, `for` and
`while` loops, dictionaries, lists, and user-defined functions.

The answers are hidden in a collapsible block under each question.
Click "Show answer" to reveal the answer and a short explanation.

Score yourself: count the questions where your final answer matches
the **expected answer**. The explanations are not graded — they're
just there so you can read what you missed.

---

### Q1 — `print` and f-strings

Given the following script, what is the **exact** output?

```python
name = "Alice"
count = 3
print(f"{name} has {count} books.")
print("Done.")
```

<details>
<summary>Show answer</summary>

**Expected output:**

```
Alice has 3 books.
Done.
```

Explanation: the f-string interpolates the values of `name` and
`count` into the string. The second `print` is a plain string, so
no interpolation. A blank line appears between them because each
`print` adds a newline at the end.
</details>

---

### Q2 — `input()` and type

What is the type of the variable `x` after this script runs and the
user types `42`?

```python
x = input("Type a number: ")
```

<details>
<summary>Show answer</summary>

**Expected answer:** `str` (string). Specifically, the value is the
string `"42"`, not the integer `42`.

Explanation: `input()` always returns a string, no matter what the
user types. To get an integer, you must explicitly convert with
`int(x) = int(input(...))`.
</details>

---

### Q3 — Data types

For each value below, write the Python data type (`int`, `float`,
`str`, or `bool`).

- a) `42`
- b) `3.14`
- c) `"hello"`
- d) `True`
- e) `0`
- f) `"42"`

<details>
<summary>Show answer</summary>

**Expected answers:**

- a) `int` — no decimal point
- b) `float` — has a decimal point
- c) `str` — wrapped in quotes
- d) `bool` — `True` or `False` only
- e) `int` — `0` is a whole number
- f) `str` — same as `"hello"`; the digits inside don't matter, the
  quotes do

Common trap: `"42"` looks like the number 42, but the quotes make
it a string. `type("42")` returns `<class 'str'>`, not `<class 'int'>`.
</details>

---

### Q4 — Type conversion

What does each of the following print?

```python
print(int("30") + 5)
print(int(3.9))
print(str(42) + "1")
```

<details>
<summary>Show answer</summary>

**Expected output:**

```
35
3
421
```

Explanation:

- `int("30")` converts the string `"30"` to the integer `30`. Then
  `30 + 5 = 35`.
- `int(3.9)` converts the float `3.9` to the integer `3` (Python
  truncates toward zero, it does **not** round).
- `str(42)` converts the integer `42` to the string `"42"`. Then
  `"42" + "1"` is string concatenation, giving `"421"`. This is
  the most common beginner trap: if the intent was `42 + 1 = 43`,
  the conversion was wrong.
</details>

---

### Q5 — `for` loop and `range()`

What does this script print?

```python
for i in range(1, 5):
    print(i)
```

<details>
<summary>Show answer</summary>

**Expected output:**

```
1
2
3
4
```

Explanation: `range(1, 5)` produces the sequence `1, 2, 3, 4` —
start is included, stop is excluded. So `5` does not appear in the
output. A very common beginner mistake is expecting `1, 2, 3, 4, 5`.
</details>

---

### Q6 — `for` vs `while`

Which loop is the natural choice for the following scenarios? Pick
`for` or `while` for each.

- a) Print every character in the string `"AWS Lambda"`.
- b) Keep asking the user to type a password until they type the
  correct one.
- c) Sum the numbers in a fixed list of 5 values.
- d) Process S3 events from a batch until the batch is empty.

<details>
<summary>Show answer</summary>

**Expected answers:**

- a) `for` — you have a fixed sequence (the string) and want to
  walk it once.
- b) `while` — you don't know how many attempts the user will need;
  keep going until a condition is met.
- c) `for` — fixed list, fixed count.
- d) `while` — the size of the batch isn't known in advance; keep
  processing until the source is empty. (You could also use `for`
  over the list, but if the batch is a stream that keeps growing,
  `while` is the natural choice.)

Rule of thumb: if you can name the sequence, use `for`. If the loop
runs "until something happens," use `while`.
</details>

---

### Q7 — Dictionaries

Given the dictionary below, what does each line print?

```python
user = {"name": "Alice", "age": 30, "city": "London"}
print(user["name"])
print(user["email"])
```

<details>
<summary>Show answer</summary>

**Expected output:**

```
Alice
```

…and then a `KeyError: 'email'` exception, which crashes the
script.

Explanation: `user["name"]` returns `"Alice"`. But `"email"` is
not a key in the dictionary, so Python raises a `KeyError`. In a
real Lambda you would guard against this with `if "email" in user:`
or use the `user.get("email")` form, which returns `None` for
missing keys.
</details>

---

### Q8 — Looping a dictionary

What does this script print?

```python
scores = {"alice": 90, "bob": 75, "carol": 88}
for name, score in scores.items():
    print(f"{name} scored {score}")
```

<details>
<summary>Show answer</summary>

**Expected output** (order is the insertion order in Python 3.7+):

```
alice scored 90
bob scored 75
carol scored 88
```

Explanation: `scores.items()` yields each `(key, value)` pair as a
tuple. The `for` loop unpacks each tuple into the loop variables
`name` and `score`. In Python 3.7+ the iteration order matches the
insertion order of the keys.
</details>

---

### Q9 — Lists

Given the list below, what does each line print?

```python
items = ["apple", "banana", "cherry", "date"]
print(items[0])
print(items[-1])
print(items[1:3])
print(len(items))
```

<details>
<summary>Show answer</summary>

**Expected output:**

```
apple
date
['banana', 'cherry']
4
```

Explanation:

- `items[0]` is the first item, `"apple"`. Python uses
  zero-based indexing.
- `items[-1]` is the last item, `"date"`. Negative indices count
  from the end.
- `items[1:3]` is a slice from index 1 up to (but not including)
  index 3 — so `["banana", "cherry"]`.
- `len(items)` is the size of the list, `4`.
</details>

---

### Q10 — Functions

What does this script print?

```python
def double(x):
    return x * 2

def add(a, b):
    return a + b

result = add(double(3), double(4))
print(result)
```

<details>
<summary>Show answer</summary>

**Expected output:**

```
14
```

Explanation, step by step:

- `double(3)` returns `3 * 2 = 6`.
- `double(4)` returns `4 * 2 = 8`.
- `add(6, 8)` returns `6 + 8 = 14`.
- `print(14)` displays `14`.

This is composition — the return value of one function is the
argument to another. Real Python is full of this pattern. A
Lambda handler that reads `event`, parses a body, calls a
helper, and returns a response is exactly the same shape.
</details>

---

## Scoring

- **10/10:** Outstanding. You can read and write the basics with
  confidence. Jump straight into Section 4 and the boto3 lectures.
- **8–9/10:** Pass. Read the explanations on the questions you
  missed, then move on. You can return to L79–L81 as a reference
  if anything else feels shaky.
- **6–7/10:** Borderline. Re-watch the lectures corresponding to
  the questions you missed, redo the hands-on scripts, then
  retake the quiz.
- **Below 6/10:** Re-do L79–L81 from scratch. Type every example
  yourself, run it, and read the output. The quiz will start to
  feel obvious after one full pass.
