# Section 3 Quiz — Python Basics Refresher

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you have attempted the question.

This quiz covers L09 (variables, types, f-strings, conditionals, loops,
functions) and L10 (comprehensions, error handling, modules, venv, boto3
client).

---

**Q1.** Which line correctly creates a string formatted with the current
value of a variable `name`?

- A. `"Hello " + name`
- B. `"Hello {name}".format(name=name)`
- C. `f"Hello {name}"`
- D. All three produce the same string, so any is correct

<details><summary>Show answer</summary>

**C — `f"Hello {name}"`.** All three produce a usable string, but the
course standard is the f-string (L09): concise, fast, and easy to read
when expressions inside `{}` get non-trivial. Option A is correct only
when `name` is already a string; mixing types (e.g. `int`) raises
`TypeError`. Option B works but is verbose for our purposes.

</details>

---

**Q2.** What is the output of `[x * 2 for x in [1, 2, 3] if x > 1]`?

- A. `[2, 4, 6]`
- B. `[4, 6]`
- C. `[2, 4]`
- D. `[1, 2, 3, 1, 2, 3]`

<details><summary>Show answer</summary>

**B — `[4, 6]`.** The comprehension filters first (`x > 1` keeps `2`
and `3`), then transforms each survivor (`x * 2`). The flow is
`[transform for item in iterable if condition]`, so the condition gates
inclusion, not the transformation.

</details>

---

**Q3.** Which of the following is **false** about `try / except /
finally` in Python?

- A. The `finally` block always runs, even if the `try` block raised.
- B. A bare `except:` clause is discouraged because it hides real bugs.
- C. `raise` without an argument, inside an `except` block, re-raises
     the original exception with its stack trace intact.
- D. If an `except` block returns a value, the `finally` block is
     skipped.

<details><summary>Show answer</summary>

**D.** `finally` runs whether the function returns, the `try` block
completes, or an exception propagates. That is the whole point of
`finally` — it is the place to release resources, close files, or log
a "done" line. A is true (cleanup guarantee), B is true (narrow
exceptions catch what you expect), C is true (`raise` re-raises the
current exception).

</details>

---

**Q4.** What is the correct way to create an isolated Python
environment and install `boto3` into it, on macOS / Linux?

- A. `pip install boto3`
- B. `python3 boto3 init`
- C. `python3 -m venv .venv && source .venv/bin/activate && pip install boto3`
- D. `brew install boto3`

<details><summary>Show answer</summary>

**C.** `python3 -m venv .venv` creates the environment, `source` it
activates it, and then `pip install boto3` installs into the active
env. Option A installs into the system/global Python, which is what we
are trying to avoid. Option D is not a real `brew` formula. Option B
is not a Python command.

</details>

---

**Q5.** Which file should capture the exact set of packages (and
versions) required to reproduce a project's environment on another
machine?

- A. `setup.cfg`
- B. `pyproject.toml`
- C. `requirements.txt`
- D. `Pipfile.lock` only

<details><summary>Show answer</summary>

**C — `requirements.txt`.** The convention in this course is
`pip freeze > requirements.txt` to produce a flat list of pinned
versions, and `pip install -r requirements.txt` on the target machine
to install them. Options A and B are used for libraries (and CDK
projects), not for the simple deployment packages Lambda uses. Option
D is the Poetry equivalent, not the convention here.

</details>

---

**Q6.** You write:

```python
import boto3
s3 = boto3.client("s3")
resp = s3.list_buckets()
print(resp["Buckets"][0]["Name"])
```

What is the type of `resp`?

- A. A `boto3.resources.s3.Bucket` object
- B. A `list` of `Bucket` objects
- C. A `dict` whose `"Buckets"` key maps to a list of dicts
- D. A JSON string

<details><summary>Show answer</summary>

**C — A `dict` whose `"Buckets"` key maps to a list of dicts.** The
`boto3.client` interface is low-level and dict-in / dict-out. Each
element in `resp["Buckets"]` is itself a `dict` with keys like
`"Name"` and `"CreationDate"`. The `boto3.resource` interface
(option A) is the higher-level, object-oriented style we will see in
L12.

</details>

---

**Q7.** What does `**kwargs` collect inside a function?

- A. Arbitrary positional arguments, packed into a tuple
- B. Arbitrary keyword arguments, packed into a dict
- C. A copy of all module-level globals
- D. Nothing — it is a syntax error outside a class

<details><summary>Show answer</summary>

**B — Arbitrary keyword arguments, packed into a dict.** `*args`
collects positional arguments into a tuple; `**kwargs` collects
keyword arguments into a dict. boto3 uses `**kwargs` heavily because
many AWS API operations take dozens of optional parameters — you only
pass the ones you care about.

</details>

---

**Q8.** A Lambda handler reads an S3 event and calls
`json.loads(event_body)`. If `event_body` is malformed, what is the
most appropriate behavior?

- A. Silently return `None` so the invocation shows as Success.
- B. `print` the error and return an empty dict.
- C. Catch `json.JSONDecodeError`, log it, and re-raise so Lambda
     marks the invocation as Failed.
- D. `raise ValueError("event")` and lose the original traceback.

<details><summary>Show answer</summary>

**C.** Logging gives you an audit trail in CloudWatch, and re-raising
with bare `raise` preserves the original stack trace. Async Lambda
triggers (S3, SQS) will retry on failure; synchronous ones
(API Gateway) will surface a 5xx to the caller. Option A hides bugs.
Option B still hides the failure. Option D drops the original
exception type and traceback, which makes debugging painful.

</details>

---

**Q9.** Which `import` style is recommended in this course?

- A. `from module import *`
- B. `import module` or `from module import name` (explicit names)
- C. Inline `__import__("module")` inside functions
- D. Anything works, it is purely stylistic

<details><summary>Show answer</summary>

**B.** Explicit imports make it obvious where each name comes from,
which is critical when reading code that uses boto3, JSON, datetime,
and a dozen AWS services. `import *` pollutes the namespace and
breaks linters. Inline `__import__` is fine in a pinch but is harder
to read and prevents static analysis.

</details>

---

**Q10.** You run `python3 l10_list_buckets.py` and see:

```
No AWS credentials found. Run `aws configure`.
```

Which exception was caught?

- A. `botocore.exceptions.ClientError`
- B. `boto3.exceptions.NoCredentials`
- C. `botocore.exceptions.NoCredentialsError`
- D. `awscli.exceptions.NoProfile`

<details><summary>Show answer</summary>

**C — `botocore.exceptions.NoCredentialsError`.** The boto3 client
sits on top of `botocore` (the underlying low-level library). When
no credentials can be resolved from the standard chain, botocore
raises `NoCredentialsError`, which the script catches to print a
friendly message. `ClientError` is the generic AWS-API error
(4xx/5xx); `boto3.exceptions` does not exist; `awscli` is a
separate CLI tool and not imported by the script.

</details>
