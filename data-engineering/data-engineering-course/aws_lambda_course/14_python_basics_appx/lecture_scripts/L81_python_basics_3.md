# L81 — Python Basics – 3: Data Type – List and Functions

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 14 — Python Basics Appendix
> **Duration target:** 8:58

## Prereqs

- L79 and L80 completed.
- Comfortable with `print`, variables, f-strings, `input`, the four
  basic types, `for`/`while` loops, and dictionaries.

## Key terms

- **List:** an ordered collection of items. Written with square
  brackets `[ ]`. Example: `["Alice", "Bob", "Charlie"]`. Lists
  can hold any mix of types and can grow or shrink at runtime.
- **Index:** the position of an item in a list. Python uses
  **zero-based indexing** — the first item is index 0, the second
  is index 1, and so on.
- **Negative index:** count from the end. `-1` is the last item,
  `-2` is the second-to-last.
- **List method:** a function that belongs to a list object. You
  call a method with the dot syntax: `my_list.append("new")`.
  Methods change the list in place.
- **`len()`:** a built-in function that returns the number of
  items in a list (or the number of characters in a string).
- **`append()`:** list method that adds one item to the end.
- **`pop()`:** list method that removes and returns the last
  item (or the item at a given index).
- **`sort()`:** list method that sorts the list in place.
- **Function (the user-defined kind):** a named, reusable block
  of code that you define yourself with the `def` keyword.
  Functions take **parameters** (inputs) and can **return** a
  value (output).
- **Parameter:** the variable inside the function definition —
  the placeholder for the input.
- **Argument:** the actual value you pass in when you call the
  function.
- **Return value:** the value a function hands back to the
  caller via the `return` keyword.

## Lecture

### 0:00 — Welcome to the last beginner lecture

This is the final beginner lecture in the appendix. By the end of
it you'll know about **lists** (the second big collection type
alongside dictionaries) and **functions** (the way you organize
reusable code). With those two ideas plus everything from L79 and
L80, you can read and write almost any Python you'll meet in this
course.

### 0:30 — Part 1: lists

A list is an ordered collection of items. You write one with
square brackets:

```python
# list_intro.py
friends = ["Alice", "Bob", "Charlie", "Diana"]
numbers = [1, 2, 3, 4, 5]
mixed = ["Alice", 30, True, 3.14]      # legal but usually avoided
empty = []                              # a list with no items
```

The order matters: the first item is `"Alice"`, the second is
`"Bob"`, and so on. Lists can hold any type of item, even
mixed types in the same list (though most code keeps one type
per list).

#### Reading items by index

Each item has a position called its **index**. Python starts
counting at zero:

```
Index:    0        1        2          3
         +--------+--------+----------+
List:    | Alice  |  Bob   | Charlie  | Diana
         +--------+--------+----------+
```

You read an item with `list_name[index]`:

```python
friends = ["Alice", "Bob", "Charlie", "Diana"]
print(friends[0])     # Alice
print(friends[1])     # Bob
print(friends[2])     # Charlie
print(friends[3])     # Diana
```

Negative indices count from the end:

```python
print(friends[-1])    # Diana   (last)
print(friends[-2])    # Charlie (second to last)
```

If you ask for an index that doesn't exist, you get an
`IndexError`:

```python
print(friends[10])
# IndexError: list index out of range
```

#### Changing items by index

Lists are **mutable** — you can change them after they're
created:

```python
friends[0] = "Alex"
print(friends)
# ['Alex', 'Bob', 'Charlie', 'Diana']
```

The first item changed from `"Alice"` to `"Alex"`. Strings
and numbers are **immutable** (you can't change `"Alice"` in
place), but lists are designed to be changed.

#### Looping over a list

We've already done this, but let's make it official:

```python
friends = ["Alice", "Bob", "Charlie", "Diana"]
for name in friends:
    print(f"Hello, {name}!")
```

If you need the index too, use `enumerate()`:

```python
for i, name in enumerate(friends):
    print(f"{i}: {name}")
```

Output:

```
0: Alice
1: Bob
2: Charlie
3: Diana
```

`enumerate()` is a built-in function that wraps any iterable
and adds a counter to each item.

#### `len()` — how big is the list?

`len()` returns the number of items:

```python
friends = ["Alice", "Bob", "Charlie", "Diana"]
print(len(friends))   # 4
```

`len()` also works on strings (returns the number of characters):

```python
print(len("hello"))   # 5
```

#### Slicing — taking a sub-list

You can take a **slice** of a list with `list[start:stop]`.
The `start` index is included; the `stop` index is not.

```python
letters = ["a", "b", "c", "d", "e", "f"]
print(letters[1:4])      # ['b', 'c', 'd']
print(letters[:3])       # ['a', 'b', 'c']  (start defaults to 0)
print(letters[3:])       # ['d', 'e', 'f']  (stop defaults to end)
print(letters[:])        # full copy
```

Slicing is a topic for later in the course. For now, just
remember it exists.

### 3:00 — Part 2: list methods

A **method** is a function that belongs to an object. You call
a method with the dot syntax: `object.method(arguments)`.
Lists come with a small set of methods that let you change
them. Here are the four you'll use most in this course.

#### `append()` — add one item to the end

```python
# append_demo.py
tasks = ["write code", "test code"]
tasks.append("deploy code")
print(tasks)
# ['write code', 'test code', 'deploy code']
```

`append()` is the workhorse of list growth. In a Lambda, you'll
often see something like:

```python
results = []
for record in event["Records"]:
    results.append(process_record(record))
```

That's "start with an empty list, then add one result per
record." The classic pattern.

#### `pop()` — remove and return the last item

```python
tasks = ["write code", "test code", "deploy code"]
last = tasks.pop()
print(last)       # deploy code
print(tasks)      # ['write code', 'test code']
```

You can also pass an index:

```python
tasks = ["write code", "test code", "deploy code"]
first = tasks.pop(0)
print(first)      # write code
print(tasks)      # ['test code', 'deploy code']
```

`pop()` is useful when you're processing a queue — "give me
the next item, take it off the front."

#### `sort()` — sort the list in place

```python
numbers = [5, 2, 8, 1, 9, 3]
numbers.sort()
print(numbers)
# [1, 2, 3, 5, 8, 9]
```

`sort()` rearranges the list in ascending order. By default
it sorts numbers numerically and strings alphabetically. To
sort in descending order, pass `reverse=True`:

```python
numbers = [5, 2, 8, 1, 9, 3]
numbers.sort(reverse=True)
print(numbers)
# [9, 8, 5, 3, 2, 1]
```

Two important notes:

- `sort()` changes the list **in place** and returns `None`.
  If you write `sorted_list = numbers.sort()`, `sorted_list`
  is `None`. To get a new sorted list without changing the
  original, use the built-in `sorted(numbers)` instead.
- `sort()` only works if the items are comparable to each
  other. You can't sort a list that mixes numbers and
  strings.

#### `in` — check if an item is in the list

`in` is a keyword, not a method, but it pairs naturally with
lists:

```python
friends = ["Alice", "Bob", "Charlie", "Diana"]
print("Alice" in friends)     # True
print("Eve" in friends)       # False
```

A very common pattern in Lambda handlers:

```python
required_keys = ["bucket", "key", "size"]
for k in required_keys:
    if k not in event:
        raise ValueError(f"Missing required key: {k}")
```

This is "for each required key, check that it's in the event;
if not, raise an error." You'll see this pattern a lot.

#### ASCII cheat sheet for the four operations

```
  LIST METHODS
  +--------------------------------------------------+
  |  my_list.append(x)   add x to the end            |
  |  my_list.pop()       remove + return the last     |
  |  my_list.pop(i)      remove + return at index i   |
  |  my_list.sort()      sort in place                |
  |  x in my_list        True if x is in the list     |
  +--------------------------------------------------+
```

### 5:30 — Part 3: functions

You've been calling functions since L79: `print(...)`, `input(...)`,
`type(...)`, `len(...)`, `range(...)`, `int(...)`. These are
**built-in** functions — Python ships with them.

Sometimes you want your own function. A function is a named
block of code that you can run any time by **calling** it.
Functions are how you organize reusable work so you don't
repeat yourself.

You define a function with the `def` keyword:

```python
def greet():
    print("Hello!")
```

That defines the function. It doesn't run yet. To run it,
**call** it by name:

```python
greet()    # Hello!
greet()    # Hello!  (called again)
```

The function body is the indented block. As with `for` and
`if`, indentation is what tells Python "these lines belong
to the function."

#### Parameters — passing input to the function

Most functions need input. You declare one or more
**parameters** in the function definition:

```python
def greet(name):
    print(f"Hello, {name}!")
```

`name` is the parameter — a placeholder for the value the
caller will pass in. The caller passes the actual value
(called the **argument**) when calling the function:

```python
greet("Alice")     # Hello, Alice!
greet("Bob")       # Hello, Bob!
```

The argument `"Alice"` is bound to the parameter `name` for
the duration of the call. You can have multiple parameters,
separated by commas:

```python
def greet(name, city):
    print(f"Hello {name} from {city}!")

greet("Alice", "London")
# Hello Alice from London!
```

The arguments are matched up **in order** — first to first,
second to second. If you mix up the order, the meaning
changes:

```python
greet("London", "Alice")
# Hello London from Alice!
```

#### Return values — getting output back

A function can also **return** a value to the caller using
the `return` keyword:

```python
def add(a, b):
    return a + b

result = add(3, 5)
print(result)        # 8
```

`return` does two things:

1. Sends the value back to the caller.
2. Exits the function immediately. Any code after `return`
   in the same block doesn't run.

A function with no `return` (or just `return` with no value)
returns `None`. `print()` returns `None` — it prints to the
screen but doesn't return anything to the caller.

#### A function that does both

```python
def full_name(first, last):
    return f"{first} {last}"

def greet(name, city):
    full = full_name(name, "Smith")   # call one function from another
    return f"Hello {full} from {city}!"

print(greet("Alice", "London"))
# Hello Alice Smith from London!
```

Notice how `greet` calls `full_name` and uses its return value.
Functions can call other functions. The return value of one
function becomes the input to another — that's how you build
up larger behavior from smaller pieces.

ASCII art of the call stack for `greet("Alice", "London")`:

```
  +------------------+
  |  greet("Alice",  |  call
  |        "London") |
  +------------------+
         |
         v
  +------------------+
  |  name  = "Alice" |
  |  city  = "London"|
  |  full  = full_name("Alice", "Smith")
  |           |     |
  |           v     |
  |     +------------------+
  |     | full_name        |
  |     | first = "Alice"  |
  |     | last  = "Smith"  |
  |     | return "Alice Smith"
  |     +------------------+
  |  return f"Hello {full} from {city}!"
  |  → returns "Hello Alice Smith from London!"
  +------------------+
         |
         v
  print(...) displays the result
```

#### A slightly bigger example — squaring numbers

```python
# square.py
def square(x):
    return x * x

numbers = [1, 2, 3, 4, 5]
squares = []

for n in numbers:
    s = square(n)
    squares.append(s)
    print(f"square({n}) = {s}")

print(f"All squares: {squares}")
```

Output:

```
square(1) = 1
square(2) = 4
square(3) = 9
square(4) = 16
square(5) = 25
All squares: [1, 4, 9, 16, 25]
```

The function `square` is defined once and called five times.
If we wanted to change "square" to "cube" we'd only edit one
line: `return x * x * x`. That's the value of functions —
change the logic in one place, and every call sees the new
behavior.

### 8:30 — Recap

In this final beginner lecture you learned:

- **Lists** — ordered collections written with `[ ]`.
- Indexing (`list[0]`, `list[-1]`) and slicing (`list[1:4]`).
- `len(list)` for size, `in` for membership.
- List methods: `append`, `pop`, `sort`.
- **Functions** — `def`, parameters, arguments, `return`.
- Calling functions from other functions.

With L79 + L80 + L81 you now have the **complete beginner's
toolkit** for this course. Every Lambda function in the rest
of the curriculum will be made of these pieces — `print`,
variables, f-strings, `input`, the four types, `for`/`while`,
dictionaries, lists, and user-defined functions.

Take the section quiz at `../../quizzes/section_14.md`. 10
questions. Score 8/10 or better, return to Section 4 (L11) and
pick up the Lambda work with confidence.

## Hands-on

1. **Build a list from input.** Create `collect_names.py`. Use
   a `while` loop to ask the user to type names. Stop when
   the user types "stop". Store each name in a list. At the
   end, print the list and its length.
2. **List methods practice.** Create `todo.py`. Start with an
   empty list `todo`. Use `append` to add three tasks. Use
   `pop` to remove the last task and print it. Print the
   remaining list. Sort the list alphabetically and print it.
3. **Membership test.** Create `valid_users.py`. Define a
   list `valid_users = ["alice", "bob", "carol"]`. Ask the
   user to type a username. Print "Welcome" if the username
   is in the list, or "Access denied" if not.
4. **First function.** Create `temp.py`. Define a function
   `celsius_to_fahrenheit(c)` that returns the Fahrenheit
   value for a Celsius input. The formula is
   `c * 9/5 + 32`. In the main script, ask the user for a
   Celsius temperature, call the function, and print the
   result.
5. **Function with a loop.** Create `total.py`. Define a
   function `total(numbers)` that takes a list of numbers
   and returns their sum. In the main script, define a list
   of five numbers, call `total`, and print the result.
6. **Stretch — combine everything.** Create `report.py`.
   Build a list of three dictionaries, each representing a
   person with `name`, `age`, and `city`. Define a function
   `summarize(person)` that returns an f-string summary.
   Use a `for` loop to call `summarize` on each person and
   print the result.

## Quiz prep

The section quiz (`../../quizzes/section_14.md`) covers everything
in L78–L81. The 10 questions are:

- `print`, variables, f-strings, `input`
- `int` / `float` / `str` / `bool` + `type()` + conversion
- `for` loops and `range()`
- `while` loops
- Dictionaries (read, write, loop, KeyError)
- Lists (read by index, `len`, `in`, methods)
- Functions (`def`, parameters, `return`)

Score 8/10 or better and you're ready for the rest of the course.

## Further reading

- **Official Python tutorial — More on Lists**
  <https://docs.python.org/3/tutorial/datastructures.html#more-on-lists>
  — every list method documented by the Python team.
- **Official Python tutorial — Defining Functions**
  <https://docs.python.org/3/tutorial/controlflow.html#defining-functions>
  — the canonical reference for `def`, parameters, and `return`.
- **Real Python — "Python lists"**
  <https://realpython.com/python-lists/> — slower-paced
  walkthrough with more examples if you want a second pass.
- **L80 (previous lecture):** `L80_python_basics_2.md` — data
  types, loops, dictionaries.
- **Section README:** `../README.md`.
- **Section quiz:** `../../quizzes/section_14.md`.
