# L80 — Python Basics – 2: Data Types Intro, For Loops and Data Type – Dictionary

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 14 — Python Basics Appendix
> **Duration target:** 13:03

## Prereqs

- L79 completed. You have PyCharm installed, a project folder ready, and
  you've written and run at least one `print` + `input` script.
- Comfortable using f-strings and assigning variables.

## Key terms

- **Data type:** the *kind* of value a variable holds. Python's four
  basic types are `int` (whole numbers), `float` (decimal numbers),
  `str` (text) and `bool` (True/False). A variable's type determines
  what you can do with it.
- **`type()`:** a built-in function that returns the type of a value
  or a variable. `type(42)` returns `<class 'int'>`.
- **Type conversion:** turning a value of one type into another type
  explicitly. `int("30")` converts the string `"30"` into the number
  `30`. `str(42)` does the opposite.
- **`for` loop:** a way to repeat a block of code once for each item
  in a sequence. "Do this thing for every name on the list."
- **`while` loop:** a way to repeat a block of code as long as a
  condition is true. "Keep asking for a password until they get it
  right."
- **Sequence:** anything Python can walk through one item at a time —
  a list, a string, a range of numbers, the lines in a file, the keys
  in a dictionary, the items returned by a Lambda.
- **`range()`:** a built-in function that produces a sequence of
  numbers. `range(5)` is `0, 1, 2, 3, 4`. `range(1, 6)` is `1, 2, 3, 4, 5`.
- **Dictionary (`dict`):** a collection of **key → value** pairs.
  You look up a value by its key, the same way you look up a word in
  a real dictionary. Example: `{"name": "Alice", "age": 30}`.
- **Key:** the "lookup word" in a dictionary. Keys must be unique
  and must be of an immutable type (usually strings or numbers).
- **Value:** the data attached to a key. Values can be any type
  — strings, numbers, lists, even other dictionaries.

## Lecture

### 0:00 — Welcome back

Last lecture you learned the four most useful beginner tools:
`print`, variables, f-strings, and `input`. With those four you can
already build small interactive scripts.

This lecture you add three more ideas: **data types** (what kind of
thing a variable holds), **loops** (how to repeat work), and
**dictionaries** (a powerful way to organize related data). These
three ideas are the foundation of almost every program you'll ever
write — including the boto3 calls in the rest of this course.

### 0:30 — Part 1: the four basic data types

So far we've been treating values as just "stuff we put in variables."
Now we'll be more precise. Every value in Python has a **type**, and
the type tells you two things: what the value *is* and what you can
*do* with it.

```python
# int — whole numbers, positive or negative, no decimal point
students = 30
temperature = -5
year = 2026

# float — decimal numbers
price = 19.99
pi = 3.14159
ratio = 0.5

# str — text, always in quotes
course_name = "AWS Lambda + Python"
emoji = ":-)"   # even "emoji" are just strings
empty = ""      # an empty string is still a string

# bool — True or False (capital T and capital F — important!)
is_lambda_event = True
is_paid = False
```

The four are easy to tell apart: `int` has no decimal point, `float`
does, `str` is in quotes, `bool` is `True` or `False` (and nothing
else).

### 1:30 — `type()` — asking Python "what is this?"

Sometimes you forget what type a variable is. Python can tell you
with the `type()` function. Try this in a new file `types.py`:

```python
# types.py

students = 30
price = 19.99
course_name = "AWS Lambda + Python"
is_active = True

print(type(students))       # <class 'int'>
print(type(price))          # <class 'float'>
print(type(course_name))    # <class 'str'>
print(type(is_active))      # <class 'bool'>
```

Output:

```
<class 'int'>
<class 'float'>
<class 'str'>
<class 'bool'>
```

`<class 'int'>` means "this is an int." The word `class` here means
"category" — Python is reporting the category the value belongs to.
The angle brackets and the word `class` look intimidating but the
useful part is just the name at the end: `int`, `float`, `str`,
`bool`.

### 2:30 — Type conversion — turning one type into another

Sometimes you have a value of one type but you need a different
type. Example: `input()` returns a string, but you want to do
arithmetic on the user's answer. The solution is to **convert**
the type explicitly.

```python
age_text = input("How old are you? ")   # age_text is a str
age = int(age_text)                     # age is an int
print(f"Next year you will be {age + 1}")
```

If the user typed `30`, `age_text` is the string `"30"`. After
`int(age_text)`, `age` is the number `30`. Now you can add `1`
and get `31` instead of `"301"`.

The four conversion functions you'll use most:

```python
int("42")        # str → int,    42
float("3.14")    # str → float,  3.14
str(42)          # int → str,    "42"
bool(0)          # int → bool,   False
```

A small trap: `int("3.14")` **fails** with a `ValueError`. You
have to go string → float → int, in two steps:

```python
int(float("3.14"))   # 3
```

### 4:00 — Part 2: `for` loops — "do this for each thing"

Real programs almost always repeat work. A Lambda that processes
S3 events has to look at every event in the batch. A script that
emails a list of users has to walk through every user. The tool
for that is a **loop**.

The most common kind of loop in Python is the `for` loop. The
shape is:

```python
for variable in sequence:
    do_something_with(variable)
```

The indented line is the **body** of the loop. It runs once for
each item in the sequence. The variable is replaced by the next
item on each pass.

Walk through this:

```python
# for_loop.py
friends = ["Alice", "Bob", "Charlie", "Diana"]

for name in friends:
    print(f"Hello, {name}!")
```

Output:

```
Hello, Alice!
Hello, Bob!
Hello, Charlie!
Hello, Diana!
```

Here is what happens, step by step:

```
Iteration 1: name = "Alice"   → prints "Hello, Alice!"
Iteration 2: name = "Bob"     → prints "Hello, Bob!"
Iteration 3: name = "Charlie" → prints "Hello, Charlie!"
Iteration 4: name = "Diana"   → prints "Hello, Diana!"
```

The variable `name` doesn't exist before the loop starts. Python
creates it fresh on each pass, gives it the next value from the
list, runs the body, then throws `name` away and creates a new
one with the next value. This is the "for each" pattern, and
you'll write it a hundred times in this course.

ASCII art of the flow:

```
    friends = ["Alice", "Bob", "Charlie", "Diana"]
              |
              v
    +---- Is there a next item? ----+
    |  No  →  done.                  |
    |  Yes →  name = next item       |
    |         run the body           |
    |         go back to the top     |
    +-------------------------------+
```

The indentation (4 spaces) is not optional. Python uses
indentation to figure out which lines belong to the loop body.
A missing or extra space is the most common beginner error.

### 6:00 — `range()` — looping a fixed number of times

Sometimes you don't have a list — you just want to repeat
something 5 times. Use `range(n)`:

```python
for i in range(5):
    print(f"Iteration {i}")
```

Output:

```
Iteration 0
Iteration 1
Iteration 2
Iteration 3
Iteration 4
```

`range(5)` is the sequence `0, 1, 2, 3, 4`. It starts at 0 by
default. If you want it to start at 1, pass two arguments:

```python
for i in range(1, 6):
    print(f"Count: {i}")
```

Output:

```
Count: 1
Count: 2
Count: 3
Count: 4
Count: 5
```

`range(start, stop)` includes `start` but **excludes** `stop`.
This trips up everyone the first time. Just remember: the stop
value is the first one **not** included.

### 7:00 — `while` loops — "keep going until something happens"

`for` is "for each thing." `while` is "as long as this condition
is true." Use `while` when you don't know in advance how many
times you'll loop.

```python
password = ""
while password != "secret":
    password = input("Enter the password: ")
print("Access granted.")
```

The loop keeps asking for a password until the user types
"secret." There's no list and no fixed count — the loop runs
zero, one, or a thousand times depending on what the user types.

A common trap with `while` is the **infinite loop** — a loop
whose condition is always true, so it never stops. Press
**Ctrl + C** in the terminal to kill a runaway script. In
PyCharm, click the red square Stop button.

### 8:00 — Part 3: dictionaries

A **dictionary** is a collection of **key → value** pairs.
The official Python name is `dict`. You create one with
curly braces `{ }`:

```python
# A dictionary describing one user
user = {
    "name": "Alice",
    "age": 30,
    "city": "London",
    "is_admin": True,
}
```

Each line is a **key: value** pair. The keys here are
`"name"`, `"age"`, `"city"`, `"is_admin"`. The values are
`"Alice"`, `30`, `"London"`, `True`. Keys must be unique
within a dictionary. Values can be anything, even another
dictionary.

The mental model: a real dictionary maps a word (key) to
a definition (value). A Python dictionary maps a key to
a value. You "look up" by key.

#### Reading values

You read a value using `[key]`:

```python
print(user["name"])      # Alice
print(user["age"])       # 30
```

If the key doesn't exist, Python raises a `KeyError`:

```python
print(user["email"])
# KeyError: 'email'
```

#### Writing values

You write a value the same way — assign to the bracket
expression:

```python
user["email"] = "alice@example.com"
print(user["email"])
# alice@example.com
```

If the key already existed, the value is overwritten. If
it didn't, the new key → value pair is added.

#### Looping over a dictionary

Three idioms, all useful:

```python
# 1. Loop over the keys
for key in user:
    print(key)

# 2. Loop over keys AND values together (most common)
for key, value in user.items():
    print(f"{key} = {value}")

# 3. Loop over just the values
for value in user.values():
    print(value)
```

Output of idiom 2:

```
name = Alice
age = 30
city = London
is_admin = True
```

The order in modern Python (3.7+) is the order in which you
inserted the keys. Don't rely on this in older Pythons, but
it's safe in the Python 3.11+ we use in this course.

#### Nested data — dictionaries inside dictionaries

Dictionaries can hold any value, including other dictionaries
and lists. Real Lambda events look exactly like this:

```python
# A simulated S3 event payload
event = {
    "Records": [
        {
            "eventName": "ObjectCreated:Put",
            "s3": {
                "bucket": {"name": "my-bucket"},
                "object": {"key": "uploads/2026/data.csv"},
            },
        },
        {
            "eventName": "ObjectCreated:Put",
            "s3": {
                "bucket": {"name": "my-bucket"},
                "object": {"key": "uploads/2026/report.pdf"},
            },
        },
    ]
}

# Walk the structure
for record in event["Records"]:
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    print(f"S3://{bucket}/{key}")
```

Output:

```
S3://my-bucket/uploads/2026/data.csv
S3://my-bucket/uploads/2026/report.pdf
```

This is exactly the shape of an S3 event in a real Lambda
function. Notice how the code reads almost like English:
"for each record, get the bucket name and the object key,
then print them." The brackets `["..."]` are how you walk
into the structure — one level at a time.

### 12:00 — Recap

In this lecture you learned:

- The four basic data types: `int`, `float`, `str`, `bool`.
- `type()` to ask what type a value is.
- Type conversion with `int()`, `float()`, `str()`, `bool()`.
- `for` loops for "do this for each thing."
- `range(n)` to repeat a fixed number of times.
- `while` loops for "keep going until something happens."
- Dictionaries: `dict`, keys, values, reading, writing, looping.
- Nested data: dictionaries inside dictionaries, which is the
  shape of every Lambda event you'll see in this course.

In L81 we finish the basics with **lists** (the other big
collection type), **list methods** (`append`, `pop`, `sort`),
and **functions** — the way you package reusable work.

## Hands-on

1. **Type guessing.** Create `type_quiz.py`. For each of these
   values, write a `print(type(...))` line:
   `42`, `3.14`, `"hello"`, `True`, `0`, `""`, `"42"`. Run it and
   make sure each line of output makes sense to you.
2. **Type conversion.** Create `age_calc.py`. Ask the user for
   their birth year. Convert to int. Print their age.
3. **Sum with a loop.** Create `sum_loop.py`. Make a list of
   five numbers, e.g. `[10, 20, 30, 40, 50]`. Use a `for` loop
   to compute the sum. Print the result. The expected sum is
   150.
4. **Word counter.** Create `word_counter.py`. Make a string
   variable that contains a sentence. Use a `for` loop to
   count how many times the letter "e" appears. Print the
   count.
5. **Phone book.** Create `phone_book.py`. Build a dictionary
   with at least four entries, each mapping a name to a phone
   number. Ask the user to type a name. Print that person's
   phone number, or "Not found" if the name is not in the book.
6. **Stretch — nested data.** Create `lambda_event.py`. Build a
   dictionary that mimics an S3 event with at least two
   records. Print the bucket name and object key of each
   record using a `for` loop.

## Quiz prep

The section quiz (`../../quizzes/section_14.md`) covers:

- Differences between `int`, `float`, `str`, `bool`.
- How to convert between types with `int()`, `str()`, etc.
- The shape of a `for name in sequence:` loop.
- What `range(1, 5)` produces.
- The difference between `for` and `while`.
- How to look up a value in a dictionary by key.
- What `KeyError` means.
- How to loop over `dict.items()` to get key + value.

## Further reading

- **Official Python tutorial — Data Structures**
  <https://docs.python.org/3/tutorial/datastructures.html#dictionaries>
  — the official "Dictionaries" section. Same content as this lecture
  in the words of the Python team.
- **Real Python — "Python for loops"**
  <https://realpython.com/python-for-loop/> — a longer, slower walk
  through `for` loops with more examples if you want a second pass.
- **L81 (next lecture):** `L81_python_basics_3.md` — lists and
  functions.
