# FCI Cluster Monitor — Code

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 15 (FCI Cluster Monitor)
> **Lectures:** L82–L87

This folder contains the runnable artifacts for the FCI Cluster Monitor use
case — the third enterprise project in the course. The handler in
`monitor_lambda/lambda_function.py` is the same code covered in L86, the
CloudFormation template in `cloudformation/fci_monitor_stack.yaml` is the
stack assembled in L87, and the test suite exercises every code path the
lectures talk about.

## Layout

```
code/
├── README.md                                ← you are here
├── monitor_lambda/
│   ├── lambda_function.py                   ← the monitor Lambda (matches L86)
│   ├── test_lambda_function.py              ← moto-based tests (7 cases)
│   └── iam_policy.json                      ← the IAM policy the Lambda needs
├── event_payloads/
│   └── scheduled_event.json                 ← example EventBridge event
└── cloudformation/
    ├── fci_monitor_stack.yaml               ← CFN template for the full stack
    └── deploy.sh                            ← bash deploy script
```

## Prerequisites

- Python 3.10+ (the handler is written in 3.11+ syntax but is
  forward-compatible back to 3.10 for the test environment).
- `boto3 >= 1.34`, `moto >= 5.0`, `pytest >= 8.0`. All are pinned in
  `../../requirements.txt`.
- For deploy: AWS CLI v2 with credentials configured (`aws configure`).
- An **existing** FSx for Windows File Server file system joined to an
  AWS Managed Microsoft AD. The CloudFormation template does *not*
  create the FSx file system — that is a heavier, one-time, in-VPC
  resource that is normally provisioned by the platform team. The
  monitor stack only needs the FSx ID.

## Run the unit tests (no AWS account required)

```bash
cd 15_fci_cluster_monitor/code
python -m venv .venv && source .venv/bin/activate
pip install -r ../../requirements.txt

cd monitor_lambda
pytest -v
```

You should see:

```
test_lambda_function.py::test_module_loads_with_defaults PASSED
test_lambda_function.py::test_handler_does_not_grow_when_above_threshold PASSED
test_lambda_function.py::test_handler_grows_when_below_threshold PASSED
test_lambda_function.py::test_handler_is_idempotent_within_cooldown PASSED
test_lambda_function.py::test_handler_returns_error_when_fsx_id_missing PASSED
test_lambda_function.py::test_handler_dry_run_does_not_call_update PASSED
test_lambda_function.py::test_local_main_block_runs PASSED
7 passed
```

> **Note on moto:** `moto 5.x` implements `fsx.create_file_system` and
> `fsx.describe_file_systems` but does **not** implement
> `fsx.update_file_system`. The grow-path tests therefore use
> `unittest.mock.patch` on the FSx client to drive the call shape and
> assert the arguments. The non-grow paths use a real `mock_aws()`
> context. See the test file's docstring for details.

## Smoke-test the handler locally

```bash
cd monitor_lambda
# Without FSX_FILE_SYSTEM_ID -> the handler returns a structured error
python lambda_function.py
# {"status": "error", "reason": "FSX_FILE_SYSTEM_ID is not set"}

# With a real FSx file system in your account
export FSX_FILE_SYSTEM_ID=fs-0123456789abcdef0
export AWS_REGION=us-east-1
python lambda_function.py
# {"status": "ok|grew|skipped|...","current_capacity_gb":...,"new_capacity_gb":...}
```

## Deploy the full stack

The CloudFormation template provisions the SNS topic + email
subscription, the Lambda, the IAM role + policy, the EventBridge
schedule, and the CloudWatch alarm on `FSx FreeStorageCapacity`.

```bash
cd 15_fci_cluster_monitor/code/cloudformation
export OPS_EMAIL=ops@example.com
export FSX_FILE_SYSTEM_ID=fs-0123456789abcdef0
./deploy.sh
```

The script:

1. zips the Lambda handler into `../monitor_lambda/monitor_lambda.zip`;
2. validates the template with `aws cloudformation validate-template`;
3. runs `aws cloudformation package` to upload the zip to a
   per-environment assets bucket and rewrite the template;
4. runs `aws cloudformation deploy` with `CAPABILITY_NAMED_IAM`
   (the template creates a role with a hardcoded name).

After deploy, the script prints the stack outputs and reminds you to
confirm the SNS email subscription.

## Tear-down

```bash
aws cloudformation delete-stack \
  --stack-name ${STACK_NAME:-fci-monitor} \
  --region ${AWS_REGION:-us-east-1}
```

The CFN assets bucket is *not* deleted automatically. Remove it
explicitly when you are done:

```bash
ASSET_BUCKET=fci-monitor-cfn-assets-dev-<account-id>-<region>
aws s3 rb "s3://${ASSET_BUCKET}" --force
```

## Hand-testing the alarm

To prove the alarm fires end-to-end, you can either:

1. **Drive the alarm via the monitor Lambda.** Set
   `THRESHOLD_GB=10000` in the parameter overrides and re-deploy;
   the next scheduled invocation will *not* grow (because 50 GiB
   < 10 000 GiB), but the alarm `fci-monitor-fsx-free-storage-low`
   fires on the CloudWatch metric and publishes to SNS.
2. **Lower the actual file system size** to below the threshold via
   the FSx console (Storage → Actions → Update storage capacity →
   shrink — note: shrinking is rarely possible in production;
   prefer option 1 for hand-tests).

You should receive an email at `${OPS_EMAIL}` within a few minutes of
the alarm transitioning to `IN_ALARM`.

## Logs Insights query

To see every grow decision in one place, run this in CloudWatch Logs
Insights against the `/aws/lambda/fci-monitor` log group:

```
fields @timestamp, @message
| filter @logGroup like /fci-monitor/
| parse @message "{\"event\": \"*\", *" as event, rest
| display @timestamp, event, rest
| sort @timestamp desc
| limit 50
```

Or, more simply, `filter event = "monitor.grew"` to see only the
successful grows.
