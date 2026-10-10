# Section 5 — Managing EC2 (L23–L26)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 5 of 8
> **Duration:** ~44 min total (L23: 12, L24: 12, L25: 12, L26: 8)
> **Working artifact:** `code/snapshot_ami_demo/snapshot_ami_demo.py` + 4 pytest tests

This section teaches the day-2 operations of an EC2 fleet: how to stop,
start, resize, and terminate instances without losing data; how to back
up EBS volumes with point-in-time snapshots; and how to bake a
gold-image AMI that you can launch a hundred times. L26 ties it all
together with a runnable demo.

## Lecture map

| L# | Title | File | Min |
|---|---|---|---|
| L23 | Stop, Start, Resize, Terminate | `lecture_scripts/L23_stop_start_resize_terminate.md` | 12 |
| L24 | EBS Snapshots | `lecture_scripts/L24_ebs_snapshots.md` | 12 |
| L25 | Custom AMIs | `lecture_scripts/L25_custom_amis.md` | 12 |
| L26 | Recap + `snapshot_ami_demo.py` | `lecture_scripts/L26_section_recap.md` | 8 |

## Working code

- `code/snapshot_ami_demo/snapshot_ami_demo.py` — boto3 script that
  takes a snapshot of an EBS volume, waits for it to complete, builds
  a new AMI from that snapshot, waits for the AMI to become
  `available`, tags the AMI, and returns both the snapshot id and the
  AMI id.
- `code/snapshot_ami_demo/test_snapshot_ami_demo.py` — 4 pytest
  tests using `@mock_aws`.
- `code/snapshot_ami_demo/README.md` — usage, IAM policy, run
  instructions.

Run the demo tests:

```bash
cd 05_managing_ec2/code/snapshot_ami_demo
pytest test_snapshot_ami_demo.py -v
```

Or from the course root:

```bash
python scripts/run_all_tests.py
```

## How to read this section

1. **L23 first.** Instance lifecycle states are the mental model on
   which L24 and L25 are built. Understand "data on the root EBS
   volume survives a stop but not a terminate" before moving on.
2. **L24 second.** A snapshot is a point-in-time copy of a single
   EBS volume. The two important properties are: (a) snapshots are
   incremental (only the changed blocks since the previous snapshot
   are stored), and (b) snapshots can be copied across regions and
   shared across accounts.
3. **L25 third.** A custom AMI packages one or more snapshots +
   launch metadata into a single, launchable artifact. AMIs are how
   you go from "one hand-configured instance" to "a fleet of 100
   identical instances."
4. **L26 last.** The recap walks through `snapshot_ami_demo.py`
   line-by-line, then runs the four pytest tests. By the end of L26
   you should be able to read the script cold and explain what each
   boto3 call is doing.

## Prereqs

- L09–L18: launching an instance, EBS volumes as the instance's
  block storage, and how `run_instances` wires them up.
- L07: instance types and the difference between `t3.micro` and
  `m5.large` (matters for the resize lecture).
- L17: security groups (the resize lecture also touches the "do I
  keep the same private IP" question).

## Quiz

`quizzes/section_5.md` — 10 questions, pass bar **7 / 10**.
