# snapshot_ami_demo

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 05 — Managing EC2
> **Companion to:** L26 (Section Recap).

Snapshot an EBS volume and register the result as a new AMI. This is
the same pipeline a Terraform `aws_ami_from_instance` resource uses
internally, written out longhand in boto3.

## What it does

1. Calls `ec2.create_snapshot(VolumeId=...)` — returns a snapshot id
   in `pending` state.
2. Polls `ec2.describe_snapshots(SnapshotIds=[...])` until
   `State == "completed"`.
3. Calls `ec2.register_image(Name=..., BlockDeviceMappings=[...])` to
   register a new AMI whose only device is the completed snapshot.
4. Polls `ec2.describe_images(ImageIds=[...])` until
   `State == "available"`.
5. Tags the new AMI with `Name`, `CreatedBy=aws_ec2_course`, and
   `CourseSection=5`.
6. Returns `{"snapshot_id": ..., "ami_id": ...}`.

## Install

From the course root:

```bash
pip install -r requirements.txt
```

## Run against moto (offline)

```bash
pytest test_snapshot_ami_demo.py -v
```

You should see 4 passing tests:

- `test_snapshot_completes`
- `test_image_created_from_snapshot`
- `test_ami_tags_propagate`
- `test_ami_block_device_mapping_references_snapshot`

## Run against real AWS

```bash
python snapshot_ami_demo.py \
    --volume-id vol-0123456789abcdef0 \
    --ami-name my-golden-image \
    --region us-east-1
```

The script prints:

```
snapshot_id=snap-0123456789abcdef0
ami_id=ami-0123456789abcdef0
```

## Required IAM policy

The principal (IAM user or role) running this script needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SnapshotAndAmi",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSnapshot",
        "ec2:DescribeSnapshots",
        "ec2:RegisterImage",
        "ec2:DescribeImages",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

Notes:

- `ec2:CreateTags` is required so the script can attach the
  `Name`, `CreatedBy`, and `CourseSection` tags to the new AMI.
- In production you would scope `Resource` to specific volumes /
  snapshots / AMIs using `iam:ResourceTag` conditions. For learning
  we grant the broad action.
- If the source volume is encrypted with a custom KMS key, the
  principal also needs `kms:Decrypt`, `kms:CreateGrant`, and
  `kms:ReEncrypt*` on that key. The default EBS key works
  out-of-the-box.

## Why poll rather than use a waiter?

boto3 ships `get_waiter("snapshot_completed")` and
`get_waiter("image_available")`, but those are not always honored by
older `moto` versions. The poll-with-`time.sleep` pattern works
identically against moto and against the real AWS API, and it is
easier to step through in a debugger. For production, prefer the
waiter when one is available.

## Files

- `snapshot_ami_demo.py` — the script.
- `test_snapshot_ami_demo.py` — 4 pytest tests using `@mock_aws`.
- `README.md` — this file.
