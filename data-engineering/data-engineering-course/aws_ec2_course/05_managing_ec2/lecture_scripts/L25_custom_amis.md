# L25 — Custom AMIs

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 05
> **Duration target:** 12:00
> **Lecture ID:** L25

## Status

Authored.

## Prereqs

- L24 (snapshots) — an AMI is, at the EBS level, one snapshot per
  device in its `BlockDeviceMappings`.
- L23 (instance states) — you create an AMI from a *stopped*
  instance, not a running one, when the workload requires a
  consistent snapshot.

## Key terms

- **AMI (Amazon Machine Image)** — a launchable template: one or more EBS snapshots (one per device) + launch permissions + architecture + virtualization type + the kernel / ramdisk id (legacy).
- **`create_image`** — the boto3 / API call that snapshots every attached EBS volume of an instance and registers the result as a new AMI. It is the atomic "bake a gold image" operation.
- **`register_image`** — register a *manually-assembled* AMI (for example from a snapshot you already have, as L26's `snapshot_ami_demo.py` does).
- **`deregister_image`** — delete the AMI. Does not delete the underlying snapshots; you must delete those separately.
- **Deprecation** — set `DeprecationTime` on the AMI to mark it for retirement. New `run_instances` calls will fail; existing instances are unaffected. The standard "soft delete" pattern for AMIs.
- **CopyImage** — copy an AMI to another region, including its `BlockDeviceMappings` and snapshots.

## Lecture

A custom AMI is the "I have configured one instance exactly the way
I want it; give me a button to launch a hundred more just like it"
primitive. It is the answer to every "I want to standardize my fleet
on a known-good image" question.

There are two ways to produce a custom AMI.

1. **From an instance: `create_image`.** The AWS API snapshots
   every attached EBS volume of the source instance and registers
   the result as a new AMI in one call. The AMI is ready when
   `describe_images(ImageIds=[ami_id])["Images"][0]["State"]`
   reaches `"available"`. This is the path the console's
   "Create image" button takes.
2. **From a snapshot: `register_image`.** You already have a
   snapshot of a root volume (from L24). You supply the snapshot
   id in `BlockDeviceMappings[0].Ebs.SnapshotId`, a device name,
   an architecture, a virtualization type, and a root-device name;
   AWS registers the result as a new AMI. This is the path
   `snapshot_ami_demo.py` takes in L26. It is also the path you
   use when copying snapshots across regions — copy the snapshot,
   register a new AMI in the destination region, and you have a
   cross-region golden image.

The reverse operation is `deregister_image(ImageId=ami_id)`. After
deregistration the AMI can no longer be launched, but the underlying
snapshots are not deleted. This is intentional: you may want to
keep the snapshot for forensic or backup reasons. If you also want
to delete the snapshot, call `delete_snapshot(SnapshotId=...)`
yourself. The convention in the EC2 console is to ask, at
deregister time, whether you also want to delete the associated
snapshots.

Soft-delete is `enable_image_deprecation` (or
`modify_image_attribute(Attribute="deprecation",
OperationType="add", Value="2026-12-31T00:00:00Z")` in older API
versions). A deprecated AMI continues to launch successfully *for
already-running workflows* but new launches will fail. Deprecation
is the right tool when you want to retire an image on a known date
without surprising anyone mid-deploy.

A few rules of thumb:

- **Bake from a stopped instance.** `create_image` will accept a
  running instance, but for a consistent filesystem you should
  stop the instance first (or quiesce the FS with `fsfreeze`).
- **Bake from a *clean* instance.** Remove secrets, hostnames, SSH
  host keys, and per-instance config before snapshotting. AMIs are
  often shared across many environments; anything baked in is
  everywhere.
- **Tag the AMI.** At minimum: `Name`, `CreatedBy`, `SourceInstance`,
  and a `BuildDate`. The `snapshot_ami_demo.py` script in L26
  demonstrates the `Name`, `CreatedBy`, and `CourseSection` tag
  pattern.
- **Keep the launch permissions tight.** By default an AMI is
  private. To share across accounts, set `LaunchPermission.add`
  with the target `UserId`. To make it public, use `Group="all"`.

## Hands-on

In the AWS console:

1. Launch a `t3.micro` Amazon Linux 2 instance.
2. SSH in, install a package (`sudo yum install -y htop`), and
   write a marker file to `/etc/motd`.
3. Stop the instance.
4. Actions → Image and templates → Create image. Name it
   `golden-amazon-linux-2-htop`.
5. Wait for the AMI to reach `available`.
6. From the AMI, launch a new instance. SSH in. Verify htop is
   installed and the motd file is present.
7. Deregister the AMI. Confirm the launch option disappears.
8. (Optional) Re-register the AMI from the underlying snapshot to
   see the alternative path.

## Quiz prep

- `create_image` snapshots all attached EBS volumes and registers a
  new AMI in one call.
- `register_image` is the lower-level call that wraps an existing
  snapshot into an AMI — the path L26's `snapshot_ami_demo.py`
  takes.
- `deregister_image` does not delete the underlying snapshots; you
  must delete those separately.
- Deprecation is a soft delete: a deprecated AMI continues to work
  for existing instances but cannot be used for new launches.

## Further reading

- [Create a custom AMI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/creating-an-ami.html)
- [Deregister your AMI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/deregister-image.html)
- [Deprecate an AMI](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ami-deprecate.html)
