# L26 — Section Recap + `snapshot_ami_demo.py`

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 05
> **Duration target:** 8:00
> **Lecture ID:** L26

## Status

Authored.

## Prereqs

- L23–L25.

## Key terms

- **`boto3.client("ec2")`** — the low-level EC2 client. Returns
  dicts, not objects. This is what `snapshot_ami_demo.py` uses.
- **`create_snapshot`** — asynchronous; returns a snapshot id in
  `pending` state. We poll until `completed`.
- **`create_image`** (from instance) vs **`register_image`** (from
  snapshot). The demo uses `register_image` with a single
  `BlockDeviceMapping`.
- **`describe_snapshots` / `describe_images`** — read-side calls
  used to poll for terminal state.

## Lecture

L23 gave us the instance lifecycle, L24 gave us the snapshot, and
L25 gave us the AMI. L26 is where we wire them together with code
that you can run offline (`moto`) or against a real AWS account.

`code/snapshot_ami_demo/snapshot_ami_demo.py` does five things in
sequence:

1. Calls `ec2.create_snapshot(VolumeId=volume_id, Description=...)`
   to start a point-in-time copy of the EBS volume. AWS returns a
   snapshot id in `pending` state immediately.
2. Polls `ec2.describe_snapshots(SnapshotIds=[snap_id])` in a loop
   with a short `time.sleep` between iterations, until
   `State == "completed"`. This is the textbook pattern for
   "wait for an async AWS call to finish."
3. Calls `ec2.register_image(Name=ami_name, RootDeviceName=...,
   VirtualizationType="hvm", BlockDeviceMappings=[{"DeviceName":
   "/dev/sda1", "Ebs": {"SnapshotId": snap_id}}])` to register a
   new AMI whose only device is the snapshot we just created.
   (`create_image` would also work, but it requires an `InstanceId`
   and snapshots every attached volume of that instance; for the
   "register a new AMI from a single existing snapshot" path, the
   right call is `register_image`.)
4. Polls `ec2.describe_images(ImageIds=[ami_id])` until
   `State == "available"`.
5. Calls `ec2.create_tags(Resources=[ami_id], Tags=[...])` to apply
   `Name`, `CreatedBy=aws_ec2_course`, and `CourseSection=5` to
   the new AMI, then returns both ids.

The script's `main()` parses `--volume-id` and `--ami-name` from
the command line, calls the workflow, and prints both ids. This is
the pattern you will see in a dozen places across the rest of the
course — every "do an AWS thing and wait for it" script looks like
this.

Why this script is worth studying in detail:

- It exercises the snapshot → AMI pipeline end-to-end, the same
  pipeline a Terraform `aws_ami_from_instance` resource uses.
- It demonstrates the right way to wait for AWS — polling
  `describe_*` rather than `time.sleep`-ing a fixed interval.
- It demonstrates the "tag everything you create" hygiene rule
  from L25.

## Hands-on

Walk through the script:

1. Read `code/snapshot_ami_demo/snapshot_ami_demo.py` top to bottom.
2. Note the `wait_for_snapshot` and `wait_for_image` helpers — both
   follow the same poll-with-sleep shape.
3. Note the `BlockDeviceMappings` parameter on `register_image`. It
   is the *only* place the script names the snapshot.
4. Note the tag list at the bottom. The three tags (`Name`,
   `CreatedBy`, `CourseSection`) are what make the AMI findable
   later in a fleet.
5. Run the tests:

   ```bash
   cd 05_managing_ec2/code/snapshot_ami_demo
   pytest test_snapshot_ami_demo.py -v
   ```

   You should see 4 passing tests:
   - `test_snapshot_completes` — snapshot id starts with `snap-`,
     state is `completed`.
   - `test_image_created_from_snapshot` — AMI id starts with `ami-`,
     state is `available`.
   - `test_ami_tags_propagate` — the three tags are present.
   - `test_ami_block_device_mapping_references_snapshot` — the BDM
     references the snapshot id we just created.

## Quiz prep

- `create_snapshot` is async; you must poll `describe_snapshots`
  until state is `completed` before using the snapshot.
- `register_image` with one `BlockDeviceMapping` is the explicit
  "wrap a snapshot in an AMI" call. (`create_image` is the
  "snapshot all volumes of an instance and register an AMI"
  call — also useful, but it requires an `InstanceId`.)
- Tags on the AMI are independent of tags on the underlying
  snapshot; you must call `create_tags` on each resource you want
  to tag.
- The polling pattern (`while state != "completed": sleep;
  describe;`) is the boto3 way to wait for a long-running
  operation when there is no waiter.

## Further reading

- `code/snapshot_ami_demo/snapshot_ami_demo.py` — the demo script
- `code/snapshot_ami_demo/README.md` — IAM policy + run
  instructions
- [register_image API reference](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RegisterImage.html)
- [create_image API reference](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateImage.html)
