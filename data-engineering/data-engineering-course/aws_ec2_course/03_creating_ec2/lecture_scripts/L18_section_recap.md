# L18 — Section Recap + `launch_instance.py`

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 8:00
> **Lecture ID:** L18

## Status

Authored.

## Prereqs

- L09–L17 (everything in section 3).

## Key terms

- **`run_instances()`** — the boto3 API call that launches one or
  more EC2 instances. Returns an `Instances` list with the new
  instance id(s).
- **`get_waiter("instance_running")`** — the boto3 waiter that
  polls `describe_instances()` until the instance state is
  `running`.
- **`TagSpecifications`** — the boto3 argument that attaches
  tags to the instance, its volumes, and its ENI at launch
  time.
- **`@mock_aws`** — the moto decorator that mocks every AWS API
  call inside the decorated function, so the test runs offline.

## Lecture

L09–L17 walked through the 7-step EC2 creation wizard: AMI,
instance type, network, storage, advanced settings, user data,
key pair, security group. Each lecture mapped one wizard screen
to a boto3 argument.

This lecture ties it all together with the working demo:
`launch_instance.py`. The script is in
`code/launch_instance/launch_instance.py`; the tests are in the
same directory.

### What the script does

A single function, `launch_instance()`, that takes:

- `ami_id` — the AMI to boot from (required);
- `instance_type` — defaults to `t3.micro`;
- `key_name` — the name of an existing key pair in the region;
- `security_group_ids` — list of `sg-...` ids;
- `subnet_id` — the subnet to launch into;
- `user_data` — an optional bash / cloud-init script;
- `name` — the value of the `Name` tag;
- `region_name` — defaults to `AWS_REGION` env or `us-east-1`;
- `ec2_client` — for tests; defaults to a real boto3 client.

It builds a `run_instances()` call with all of those, attaches
the three tags we use throughout the course
(`Name`, `CreatedBy=aws_ec2_course`, `CourseSection=3`), and
returns the new instance id after the `instance_running` waiter
returns.

### The CLI

```bash
python launch_instance.py \
  --ami-id ami-0abcdef1234567890 \
  --key-name my-course-key \
  --security-group-ids sg-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0 \
  --user-data-file ./bootstrap.sh \
  --name demo-instance
```

Defaults: `instance_type=t3.micro`, `region=us-east-1`. The
script prints the instance id and (best-effort) the public DNS
name when the waiter returns.

### The tests

Six pytest tests, all under `@mock_aws`:

| Test | What it checks |
|---|---|
| `test_launch_returns_instance_id` | The return value starts with `i-`. |
| `test_launch_with_user_data_attaches_user_data` | The supplied `UserData` is passed to `run_instances()`. |
| `test_launch_tags_propagate` | `Name`, `CreatedBy`, and `CourseSection` are set on the instance. |
| `test_launch_with_default_t3_micro` | With no `instance_type`, the result is `t3.micro`. |
| `test_launch_with_custom_ami` | A custom ami id (`ami-12345`) flows through without raising. |
| `test_launch_waits_for_running` | The `instance_running` waiter is awaited at least once with the right instance id. |

Run them from the `code/launch_instance/` directory:

```bash
python -m pytest -v
```

Expected: **6 passed** in under 15 seconds, zero AWS calls.

### What we deliberately did not include

The script is intentionally **minimal**. It does not:

- attach an IAM instance profile (no API calls are made from
  inside the instance);
- configure EBS block device mappings (we use the AMI's
  defaults);
- enable detailed monitoring or termination protection (those
  are the right defaults for a learning environment; flip them
  in the wizard for production);
- create the VPC, subnet, security group, or key pair. The
  script assumes they already exist (in moto or in real AWS).

Adding each of those is an exercise for section 5 ("Managing
EC2") and section 6 ("Load Balancing"), where we wrap the
launch in higher-level abstractions.

## Hands-on

Walk through the script line-by-line.

1. **CLI parsing.** Open `launch_instance.py` and look at
   `_parse_args()`. Note that the user-data file is read **after**
   parsing — if the path is wrong, the script fails with a
   `FileNotFoundError` before any AWS call is made.

2. **The `run_instances()` call.** Look at the `run_kwargs` dict
   in `launch_instance()`. Every key matches a wizard screen from
   L09–L17:
   - `ImageId` — L10.
   - `InstanceType` — L11.
   - `KeyName` — L16.
   - `SecurityGroupIds` + `SubnetId` — L12, L17.
   - `TagSpecifications` — L09 (step 1).
   - `UserData` (conditional) — L15.

3. **The waiter.** Look at:

   ```python
   waiter = client.get_waiter("instance_running")
   waiter.wait(InstanceIds=[instance_id])
   ```

   This is what stops the script from returning before the
   instance is reachable. Without the waiter, `run_instances`
   returns as soon as AWS has **accepted** the request — not
   when the instance is up.

4. **The `if user_data:` guard.** If the user does not pass
   `--user-data-file`, the `UserData` key is **omitted entirely**
   from the `run_instances` call (rather than being passed as
   `None`). This is deliberate: `None` is a common source of
   silent type errors in boto3.

5. **The `ec2_client` parameter.** In the test, we pass a
   `@mock_aws` client so the call never leaves the test process.
   In real-AWS usage, the parameter is omitted and the function
   constructs its own client with the right region.

6. **The 6 tests.** Read `test_launch_instance.py`. The
   `ec2_setup` fixture creates a VPC, subnet, security group,
   key pair, and a fake AMI in a mocked region, then yields
   them to the test bodies. Each test is small; the pattern is
   "do the call, then describe what happened, then assert".

7. **Run the tests.** From `code/launch_instance/`:

   ```bash
   python -m pytest -v
   ```

   You should see:

   ```text
   test_launch_instance.py::test_launch_returns_instance_id PASSED
   test_launch_instance.py::test_launch_with_user_data_attaches_user_data PASSED
   test_launch_instance.py::test_launch_tags_propagate PASSED
   test_launch_instance.py::test_launch_with_default_t3_micro PASSED
   test_launch_instance.py::test_launch_with_custom_ami PASSED
   test_launch_instance.py::test_launch_waits_for_running PASSED
   6 passed in ~15s
   ```

## Quiz prep

- What's the boto3 keyword for "what AMI do I boot from"?
  (`ImageId`.)
- What's the boto3 keyword for "what key pair to inject"?
  (`KeyName` — the **name** of the key pair, not the file.)
- What does the `instance_running` waiter do? (Polls
  `describe_instances` until `State.Name == "running"`, then
  returns.)
- Which three tags does `launch_instance.py` set on every
  instance? (`Name`, `CreatedBy=aws_ec2_course`,
  `CourseSection=3`.)

## Further reading

- boto3 docs: *EC2 — `run_instances`* — <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/run_instances.html>
- boto3 docs: *EC2 — `InstanceRunning` waiter* — <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/waiter/InstanceRunning.html>
- moto docs: *EC2* — <https://docs.getmoto.org/en/latest/docs/services/ec2.html>
