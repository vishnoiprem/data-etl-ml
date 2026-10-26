# Assignment 1 — Boto3 S3 Explorer Mini-Project

> **Section:** 4 (Lambda with S3, EC2, DynamoDB)
> **Estimated time:** 4 hours
> **Deliverable:** `mini_project.py` + `test_mini_project.py` (using `moto`)
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Learning objectives

By the end of this assignment you will be able to:

1. Initialize a `boto3` session and switch between **client** and **resource** APIs deliberately.
2. Use the **paginator** API to list a variable number of S3 objects without hitting `1,000-item` truncation.
3. Distinguish the most common `ClientError` codes (`NoSuchBucket`, `AccessDenied`, `NoSuchKey`, `AllAccessDisabled`) and surface them to a user.
4. Write a small, single-file **CLI tool** with `argparse` and `input()` that behaves predictably against both real AWS and `moto` fakes.
5. Write **pytest** tests that mock AWS with `moto` so the tool can be exercised without any network or credentials.

## Background

In section 4 lectures L13–L15 you wrote one-shot scripts that create, list, and delete a single S3 bucket. This assignment is a small consolidation: build a single CLI that a colleague could use on day one to audit the buckets in a new AWS account.

The tool does exactly three things:

1. List every bucket in the account (`s3:ListAllMyBuckets`).
2. Prompt the user to pick one (or accept `--bucket` on the CLI).
3. List every object in that bucket, with size, last-modified, and storage class — paginated.

It must fail gracefully if the account has no buckets, if the user types a name that does not exist, or if the bucket has more than 1,000 objects.

## Step-by-step tasks

### Step 1 — Scaffold the project

Create the following layout inside the repo (the assignment does not ship its own `code/` folder — drop it under the section 4 code dir, or anywhere convenient):

```
04_lambda_with_aws_resources/code/boto3_mini_project/
├── README.md
├── mini_project.py
└── test_mini_project.py
```

Add a `requirements-dev.txt` (or reuse the course root `requirements.txt`):

```
boto3>=1.34
moto[s3]>=5.0
pytest>=8.0
```

### Step 2 — Implement `mini_project.py`

The file must expose three pure functions plus a `main()`:

```python
def list_buckets(session: boto3.Session) -> list[dict[str, Any]]: ...
def list_objects(session: boto3.Session, bucket: str) -> list[dict[str, Any]]: ...
def format_table(rows: Iterable[Mapping[str, Any]]) -> str: ...
def main(argv: list[str] | None = None) -> int: ...
```

Hard requirements:

- Accept `--region`, `--profile`, and `--bucket` on `argparse`. When `--bucket` is omitted, **interactively** prompt the user with `input("> ")`.
- Build the session as `boto3.Session(profile_name=..., region_name=...)`. Never hard-code credentials.
- `list_buckets()` must call `s3_client.list_buckets()` and return a list of `{"Name": ..., "CreationDate": ...}` dicts. If the list is empty, print a clear message and return a non-zero exit code.
- `list_objects()` must use `s3_client.get_paginator("list_objects_v2")` and accumulate `Contents` (and handle the `Contents` key being absent for empty buckets). Use `PaginationConfig={"PageSize": 100}`.
- `format_table()` should return a `str` with aligned columns: `Key`, `Size` (right-aligned, comma-separated bytes), `LastModified`, `StorageClass`. Use `str.rjust()` and the `humanize` trick `f"{size:,}"`.
- All user-facing errors should be caught at the CLI boundary, not in the pure functions. Use `botocore.exceptions.ClientError` and inspect `e.response["Error"]["Code"]`:
  - `NoSuchBucket` -> print `"Bucket '<name>' does not exist."` and return `2`.
  - `AccessDenied` -> print `"Access denied for bucket '<name>'."` and return `3`.
  - `AllAccessDisabled` (all buckets in account disabled) -> print a clear message and return `4`.
- Use `logging` (not `print()`) inside the pure functions; let `main()` decide whether to print a table or log JSON.

### Step 3 — Write tests with `moto`

`test_mini_project.py` must contain at least these test cases, all using the `moto` `@mock_aws` decorator:

| Test | Asserts |
|---|---|
| `test_list_buckets_empty_account` | `list_buckets` returns `[]` and `main` exits with code `1`. |
| `test_list_buckets_with_two` | After `create_bucket` x2, `list_buckets` returns both names. |
| `test_list_objects_paginates` | Put 2,500 objects via a fixture, then call `list_objects` and assert length is 2,500 (proves pagination works). |
| `test_list_objects_bucket_not_found` | Calling `list_objects("missing-bucket")` raises `ClientError` with code `NoSuchBucket` (do **not** swallow it in the pure function). |
| `test_cli_with_bucket_flag` | Run `main(["--bucket", "x", "--profile", "x"])` and assert exit code `0` after mocking. |
| `test_cli_prompts_for_bucket` | Patch `builtins.input` to return `"my-bucket"` and assert the tool picks it. |
| `test_format_table_alignment` | Call `format_table` on a 3-row fixture and assert the rendered string has padded columns. |
| `test_cli_exit_codes` | One test per documented exit code (1, 2, 3). |

Use `moto.mock_aws` as a **class decorator** on each test class, or as a context manager, so the mock is scoped per test. Do not rely on a single module-level mock.

### Step 4 — Manual smoke test

With valid AWS credentials (or `aws sso login`):

```bash
python mini_project.py --region us-east-1
# pick a bucket
# verify the table renders
python mini_project.py --region us-east-1 --bucket some-bucket
```

Then re-run the test suite:

```bash
pytest test_mini_project.py -v
```

## Deliverables

- [ ] `mini_project.py` (~150 lines, fully type-hinted, no `Any` outside `boto3` payload dicts).
- [ ] `test_mini_project.py` (>= 8 tests, all passing under `moto 5.x`).
- [ ] `README.md` with install, run, and test instructions.
- [ ] Output of `pytest -v` pasted into the PR description (text, not screenshot).
- [ ] (Stretch) `--format json` flag that emits the same data as JSON for piping into `jq`.

## Grading rubric (100 points)

| Category | Points | What we look for |
|---|---|---|
| `list_buckets` correctness | 15 | Pure function, no side effects, handles empty account. |
| `list_objects` pagination | 20 | Uses `get_paginator("list_objects_v2")`, handles `Contents is None`, handles prefixes only. |
| Error handling | 20 | All three `ClientError` codes mapped to a distinct exit code and message. No bare `except Exception`. |
| CLI design | 15 | `argparse` for flags, `input()` only when interactive, `--bucket` overrides. |
| Tests | 20 | 8+ tests, all green, all use `moto`, asserts on **behavior** not on log strings. |
| Code quality | 10 | Type hints, no `print` inside pure functions, `logging` configured once. |

Deductions:

- `-10` if a `try/except` is broad enough to swallow `KeyboardInterrupt`.
- `-5` per missing test from the table above.
- `-5` if `moto` is imported at module top level (it must be test-scoped).

## Stretch goals (optional, +10 each, capped at +20)

- Add a `--human-readable` flag that uses `humanize.naturalsize()` to render MB/GB.
- Add a `--prefix` argument that filters by key prefix without iterating the whole bucket.
- Replace `input()` with `simple_term_menu` (or `inquirer`) for arrow-key selection.

## Hints

- `moto` 5.x renamed the decorator to `mock_aws`; the older `@mock_s3` still works but emits a `DeprecationWarning`.
- `list_objects_v2` returns a `Contents` key only when there is at least one matching object. An empty bucket yields `{}`. Test for that.
- For the pagination test, create the 2,500 keys with `put_object` in a loop — there's no `put_objects` bulk API in boto3.
- When asserting on `ClientError`, use `pytest.raises(ClientError) as exc` and check `exc.value.response["Error"]["Code"] == "NoSuchBucket"`.
