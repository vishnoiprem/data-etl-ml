# 15 — Getting Started with AWS Lambda

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Getting Started with AWS Lambda."** One Python handler, six test events,
zero AWS credentials needed for verification. Drop this into `sam local
invoke` for a real run, or just point pytest at it.

```
   test-event.json ──▶  HelloLambdaFunction  ──▶  response (printed) + CloudWatch Logs
                             │
                             ├─ _greet       (name → "Hello, <name>!")
                             ├─ _factorial   (n   → n!)
                             ├─ _schedule    (EventBridge payload shape)
                             ├─ _apigw       (proxy integration response)
                             ├─ _echo        (returns event verbatim)
                             └─ _raise_error (deliberately fails)
```

## Files

| Path                              | Purpose                                           |
|-----------------------------------|---------------------------------------------------|
| `lambda_function/app.py`          | The handler -- 6 operations, 1 dispatch            |
| `template.yaml`                   | SAM template (no event source; manual invocation) |
| `events/01_greet.json` … `06_error.json` | Six named test events (the lab's "configure a test event" stage) |
| `tests/test_handler.py`           | 10 pytest tests, no AWS creds                     |
| `01_invoke_test_event.py`         | Self-asserting driver (datavidhya style)          |
| `README.md`                       | This file                                         |

## The 6 lab stages — mapped to artifacts

| Stage | Lab step                                                    | Artifact                                             |
|-------|-------------------------------------------------------------|------------------------------------------------------|
| 1     | Create a Lambda function from scratch in the console        | `template.yaml` (HelloLambdaFunction)                |
| 2     | Author the Python handler code                             | `lambda_function/app.py` (`lambda_handler` + 6 ops)  |
| 3     | Configure and run a test event                              | `events/01_greet.json` through `events/06_error.json` |
| 4     | Interpret execution results: response, duration, memory     | `tests/test_handler.py::ctx` fixture + driver        |
| 5     | Read log output in Amazon CloudWatch Logs                   | `LOG.info(...)` calls in `app.py`                    |
| 6     | Review the failure path (raising an exception)              | `06_error.json` invokes `_raise_error`               |

## Run it offline

```bash
cd medium/meta/datavidhya/15_Getting_Started_With_AWS_Lambda/

# Self-asserting driver -- 9 checks, all PASS.
../../../.env/bin/python 01_invoke_test_event.py

# pytest suite -- 10 unit tests.
../../../.env/bin/python -m pytest tests/ -v
```

Both invoke `app.lambda_handler` directly with `events/*.json` payloads --
no AWS account needed.

## Deploy to AWS (when you're ready)

```bash
sam build                                                # produces .aws-sam/
sam deploy --guided                                      # creates the stack
# After the first deploy, samconfig.toml remembers settings.
sam logs -n HelloLambdaFunction --tail                   # stream CloudWatch
```

When prompted for the IAM role, use the lab's `LambdaIntroLabRole-…` so
CloudWatch Logs writes succeed.

## What the handler actually does

The handler is a thin dispatcher. It reads `event["operation"]` (default
`"greet"`) and routes to one of six helpers:

| Operation   | Input key                                  | Output                                                     |
|-------------|--------------------------------------------|------------------------------------------------------------|
| `greet`     | `name` (default `"world"`)                 | `{"message": "Hello, <name>!", "name": <name>}`           |
| `factorial` | `n` (int, 0 ≤ n ≤ 20)                      | `{"n": n, "result": n!}`                                   |
| `echo`      | any keys                                   | the entire event, returned verbatim                        |
| `schedule`  | EventBridge rule payload                   | `{"source", "rule", "time"}`                               |
| `apigw`     | `queryStringParameters.name`               | API Gateway proxy integration response shape               |
| `error`     | `message`                                  | raises `ValueError(message)`                               |

Unknown operations return `{"echo": <event>, "warning": "unknown operation: ..."}`
rather than raising -- never silently drop a lab user's input.

## CloudWatch Logs behaviour

The handler uses Python's standard `logging` module. When deployed:

- Each invocation appends 1–3 lines to a CloudWatch log group named
  `/aws/lambda/HelloLambdaFunction`.
- The format is JSON (set via `Globals.Function.LoggingConfig.LogFormat`).
- Failures (`_raise_error`) record an `ERROR` line plus the standard
  Lambda traceback blurb.
- Read with `sam logs -n HelloLambdaFunction --tail` or the console's
  "Monitor" tab → "View CloudWatch logs".

## Lab traps the code deliberately exercises

- **Default operation = greet.** An empty event still produces output.
  Forgetting to set `operation` does NOT crash the function.
- **Factorial cap at 20.** 21! overflows 64-bit ints; the handler raises
  `ValueError("too large for n=21")` rather than silently truncating.
- **Negative factorial.** `factorial(-1)` raises `ValueError("factorial
  undefined for negative n=-1")`. The lab's read-the-logs step is moot
  without a deliberate error path.
- **`error` MUST raise.** Wrapping it in `try/except` and returning
  `{"caught": True}` makes the CloudWatch failure path look identical
  to a success. The handler raises and lets Lambda record the trace.
- **APIGW response shape matters.** Lab students who return a bare
  `{"message": "..."}` skip the proxy integration and break the API
  response. The handler returns `statusCode` + `headers` + `body`.

## Going to production

Three things to add before this leaves the lab:

1. **An event source.** Currently the function is invocation-only. Add
   `Events.Schedule: Type: Schedule` (or `Events.S3Put: Type: S3`) to
   the SAM block to wire it to a real trigger.
2. **VPC config** if the function needs to reach RDS or ElastiCache:
   ```yaml
   VpcConfig:
     SecurityGroupIds: [!Ref LambdaSg]
     SubnetIds: !Ref LambdaSubnets
   ```
3. **Reserved concurrency** to cap concurrent invocations:
   ```yaml
   ReservedConcurrentExecutions: 5
   ```
   Without this, a noisy trigger could exhaust the account-wide
   concurrency limit.

## Verification

The lab's "lab complete" check is: a function deploys, takes a test
event, returns the expected response, and the LOG lines appear in
CloudWatch. The driver and pytest here exercise the first three
sub-steps without AWS; deploying and reading CloudWatch are documented
above for the local SAM command and `sam logs`.
