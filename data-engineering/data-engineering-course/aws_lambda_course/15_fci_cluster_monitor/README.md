# Section 15 — Enterprise Use Case 3: FCI Cluster Monitor (AWS MS AD, FSx, Lambda, SNS, CloudWatch, EventBridge)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 15
> **Lectures:** L82–L87
> **Total runtime:** ~51 min
> **Status:** New section. Authored for the third enterprise use case.

This section is the third of three end-to-end **enterprise use cases** in the
course. Where section 6 was a fully event-driven file pipeline and section 8
was a serverless CRUD API, this section tackles an **operations problem**:
monitoring the free storage on a Windows file system joined to an AWS
Managed Microsoft AD directory, and *automatically* growing the volume
when free space runs low. SNS notifies ops when CloudWatch flags the file
system, and the monitor Lambda itself is scheduled by EventBridge.

The shape of the system is intentionally small but the *production
discipline* is the same as sections 6 and 8:

- a clean **scheduled, push-based architecture** (EventBridge → Lambda)
  — no polling servers, no EC2 cron;
- an FSx for Windows File Server file system joined to **AWS Managed
  Microsoft AD** (so that the FCI cluster's Windows users get real
  NTFS-style identity, not local Windows accounts);
- a **least-privilege IAM execution role** for the Lambda function
  (`fsx:DescribeFileSystems`, `fsx:UpdateFileSystem`, `sns:Publish`,
  CloudWatch Logs);
- an **SNS topic + email subscription** that ops actually reads;
- a **CloudWatch alarm** on the `AWS/FSx FreeStorageCapacity` metric
  that pages ops when the file system is genuinely low;
- an **idempotent, structured-logging Lambda** that grows the volume
  in 20 % increments with a configurable cooldown so a stuck EventBridge
  rule cannot repeatedly grow the file system;
- a `pytest` test suite using `moto.mock_aws` so the same code runs
  locally without touching AWS;
- a **CloudFormation template** that provisions the whole stack from
  one declarative file.

By the end of these six lectures you will have a working, scheduled,
self-healing storage monitor that you can deploy from a single
`deploy.sh` call.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L82 | Section Overview | 0:30 | `lecture_scripts/L82_section_overview.md` |
| L83 | Architecture — FCI Cluster Storage Monitor | 6:00 | `lecture_scripts/L83_architecture.md` |
| L84 | AWS Managed Microsoft AD 101 | 8:00 | `lecture_scripts/L84_aws_ms_ad.md` |
| L85 | Amazon FSx for Windows File Server 101 | 10:00 | `lecture_scripts/L85_fsx.md` |
| L86 | The Monitor Lambda — check storage + grow volume | 15:00 | `lecture_scripts/L86_monitor_lambda.md` |
| L87 | SNS notification + CloudWatch alarm + EventBridge schedule | 12:00 | `lecture_scripts/L87_sns_cw_eventbridge.md` |

## Code layout

```
15_fci_cluster_monitor/
├── README.md                           ← this file
├── lecture_scripts/
│   ├── L82_section_overview.md
│   ├── L83_architecture.md
│   ├── L84_aws_ms_ad.md
│   ├── L85_fsx.md
│   ├── L86_monitor_lambda.md
│   └── L87_sns_cw_eventbridge.md
├── code/
│   ├── README.md                       ← deploy + tear-down
│   ├── monitor_lambda/
│   │   ├── lambda_function.py          ← the monitor Lambda
│   │   ├── test_lambda_function.py     ← 7 moto-based tests
│   │   └── iam_policy.json             ← the Lambda's IAM policy
│   ├── event_payloads/
│   │   └── scheduled_event.json        ← example EventBridge event
│   └── cloudformation/
│       ├── fci_monitor_stack.yaml      ← full CFN template
│       └── deploy.sh                   ← bash deploy script
└── assignments/                        ← (assignment is in /assignments/)
```

## Running the lab locally

```bash
cd 15_fci_cluster_monitor/code
python -m venv .venv && source .venv/bin/activate
pip install -r ../../requirements.txt

# Run the unit tests (no AWS account required)
cd monitor_lambda
pytest -v
```

## What you build

A Lambda function `fci-monitor` that, every 5 minutes:

1. reads the FSx file system ID from the `FSX_FILE_SYSTEM_ID` env var;
2. calls `fsx.describe_file_systems` to get the current
   `StorageCapacity` (GiB) and `Lifecycle`;
3. if `Lifecycle` is not `AVAILABLE`/`UPDATING`, logs and returns;
4. if `StorageCapacity >= THRESHOLD_GB`, logs and returns;
5. if a previous grow is still inside the `COOLDOWN_SECONDS` window,
   logs and returns;
6. otherwise calls `fsx.update_file_system` with the new capacity
   (current × `GROW_FACTOR`, rounded up to the next 10 GiB);
7. emits one structured JSON log line per decision;
8. returns a structured `{status, current_capacity_gb, new_capacity_gb,
   grew, reason}` summary that EventBridge and CloudWatch can parse.

A CloudWatch alarm on `AWS/FSx FreeStorageCapacity` < `ThresholdGb`
publishes to an SNS topic with an email subscription to ops. Ops sees
the alarm, the structured logs, and (when the cooldown elapses) the
Lambda's automatic grow.

## Matching quiz

`quizzes/section_15.md` — 10 multiple-choice questions on AWS Managed
Microsoft AD, FSx for Windows, EventBridge schedules, CloudWatch
alarms, and idempotent grow logic.

## Matching assignment

`assignments/assignment_7_fci_monitor.md` — 8 h graded task: deploy the
full FCI Cluster Monitor stack, write a CloudFormation template for it,
and add a Slack notification in addition to SNS.
