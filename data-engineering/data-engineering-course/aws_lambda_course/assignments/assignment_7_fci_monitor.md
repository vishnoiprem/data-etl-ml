# Assignment 7 — FCI Cluster Monitor (and a Linux EBS Variant)

> **Optional extension exercise.** Combines the L82–L87 material with
> the broader patterns from sections 6 and 8.

## Goal

You have two related deliverables. Pick the one that matches the
workload you actually run in production.

### Deliverable A — Linux EBS variant

Re-implement the FCI Cluster Monitor for **EBS volumes on EC2**:

1. Replace `fsx:DescribeFileSystems` with `ec2:DescribeVolumes` (you
   only need the `Size` and `VolumeId` of the target volume).
2. Replace `fsx:UpdateFileSystem` with `ec2:ModifyVolume`
   (`Size=<new_size>`).
3. Keep the same EventBridge schedule, the same SNS topic, and the
   same `dry_run` flag.
4. Add a CloudWatch alarm on the `EBSVolumeIdle` or
   `VolumeConsumedReadWriteOps` metric for the target volume.
5. Write a `tests/test_ebs_monitor.py` that uses moto to drive the
   handler and asserts on the modify call.

### Deliverable B — Windows FCI variant

Stand up a real FCI cluster on AWS:

1. Deploy the CloudFormation stack from
   `15_fci_cluster_monitor/code/cloudformation/fci_monitor_stack.yaml`
   with `DryRun=false` and a valid `FileSystemId` for an FSx for
   Windows file system you own.
2. Subscribe your real email to the SNS topic (the stack creates
   the topic but not the subscription — add it from the console).
3. Push the file system close to its free-space threshold (upload
   a 100 GB file) and watch the monitor grow it within 5 minutes.
4. Capture the CloudWatch alarm state transition and the SNS
   message in a short `NOTES.md`.

## Steps

For both deliverables, the steps are the same as section 15's
hands-on flow, with the API swap above. Re-use the test fixture
in `code/event_payloads/scheduled_event.json` as your starting
point.

## Deliverable

A PR that adds:
- `code/ebs_monitor/` (or `code/fci_real_deploy/`) with the new
  handler, IAM policy, and test file
- A `Makefile` or `bootstrap.sh` that runs the test suite and (for
  Deliverable B) the deploy
- A short `NOTES.md` with one architecture decision you made
  (e.g. "I used `ec2:DescribeVolumes` + `ec2:ModifyVolume` instead
  of `cloudwatch:GetMetricData` because...)

## Bonus

- Add a `panic` mode: if the file system is *less than 5%* free,
  publish to a separate, higher-priority SNS topic.
- Add a Slack notification via the AWS Chatbot integration in
  addition to the email.
- Add a cost guard: refuse to grow the volume if doing so would
  exceed a per-month budget (read the volume price from the
  pricing API and compare to the budget stored in SSM Parameter
  Store).
