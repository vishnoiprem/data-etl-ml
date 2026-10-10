# L24 — EBS Snapshots

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 05
> **Duration target:** 12:00
> **Lecture ID:** L24

## Status

Authored.

## Prereqs

- L13 (storage volumes) — root EBS volume, `DeleteOnTermination`.
- L23 (instance states) — when to stop before snapshotting.

## Key terms

- **Snapshot** — a point-in-time copy of an EBS volume, stored in S3 (managed by AWS, not directly visible in your S3 buckets).
- **Incremental** — only the blocks that changed since the previous snapshot are written. The full volume is recoverable from any single snapshot.
- **Snapshot copy** — replicate a snapshot into another region for DR, cross-region migration, or to share with an account in another region.
- **Snapshot share (modify_snapshot_attribute)** — grant another AWS account permission to copy your snapshot into a volume they own.
- **Data lifecycle manager (DLM)** — a service that automates snapshot creation and retention with a schedule; covered in the further-reading list.

## Lecture

A snapshot is the unit of backup for an EBS volume. It is a
point-in-time copy. Once `create_snapshot` returns and the snapshot
reaches state `completed`, you can recover the entire volume from
that snapshot alone — you do not need the original volume, and you
do not need any other snapshot in the chain.

The most important property to internalize is that snapshots are
**incremental**. The first snapshot of a 100 GiB volume writes
roughly 100 GiB. The second snapshot, taken after 1 GiB of writes,
writes roughly 1 GiB. The third, after another 0.5 GiB of writes,
writes roughly 0.5 GiB. But the full 100 GiB is still recoverable
from *any one* of those snapshots. AWS achieves this by tracking
block-level references and assembling the right set of blocks at
restore time. The cost you see on your bill is the cumulative size
of all snapshots, not 3 × 100 GiB.

When do you snapshot? Three common patterns:

1. **Backup before a risky change.** Before upgrading a database
   engine, before resizing a volume, before applying OS patches,
   take a snapshot. If the change goes badly, you can restore in
   minutes.
2. **Scheduled backup.** A daily or hourly snapshot, retained for
   N days, gives you a point-in-time recovery window. AWS Data
   Lifecycle Manager is the right tool for this; the boto3
   `create_snapshots` (plural) API is the lower-level primitive.
3. **Golden image source.** Take a snapshot of a hand-configured
   root volume, then `register_image` to wrap it in an AMI. That is
   the L25 story; here we just care about producing the snapshot.

The create-snapshot API is asynchronous at two levels: the
`create_snapshot` call returns immediately with the snapshot in
`pending` state, and AWS copies the blocks in the background. The
snapshot becomes usable for restore once `describe_snapshots` shows
state `completed`. For most volumes the copy is fast (seconds to a
few minutes), but for large, heavily-changed volumes it can take
much longer. The right pattern in code is to poll
`describe_snapshots` until `State == "completed"`. (The snapshot
itself can be created from a `running` instance, but the
recommended pattern for consistency is to take it from a *stopped*
instance or to briefly quiesce the filesystem with `fsfreeze`. For
this course we accept the running-instance snapshot.)

Snapshots are regional. A snapshot created in `us-east-1` cannot be
directly attached to an instance in `eu-west-1`. To use a snapshot
in another region, call `copy_snapshot(SourceSnapshotId=...,
SourceRegion="us-east-1", DestinationRegion="eu-west-1")`. The
copy is a full copy of the data in the destination region — it is
not incremental across regions. Cross-region copies are the
foundation of most DR strategies.

You can also share a snapshot with another AWS account. By default
a snapshot is private to the account that created it. Call
`modify_snapshot_attribute(SnapshotId=..., Attribute="createVolume",
OperationType="add", UserIds=["123456789012"])` to grant
`123456789012` permission to copy the snapshot into a volume they
own in the same region. To share publicly (don't), use
`Group="all"`. To encrypt a shared snapshot, the destination
account must also be able to use the KMS key — sharing an
encrypted snapshot requires re-granting the `kms:Decrypt` /
`kms:CreateGrant` permissions on the key.

## Hands-on

In the AWS console:

1. Pick a running EBS-backed instance and identify its root volume
   id.
2. `ec2.create_snapshot(VolumeId=vol-...)`. Note the snapshot id.
3. Poll `describe_snapshots` (or use the console's "Snapshots" page)
   until state is `completed`.
4. From the snapshot, `ec2.create_volume(SnapshotId=...,
   AvailabilityZone="us-east-1a")`. Attach it to a test instance as
   `/dev/sdf` and mount it; verify the original data is visible.
5. `ec2.copy_snapshot(SourceSnapshotId=..., SourceRegion="us-east-1",
   DestinationRegion="us-west-2")`. Confirm the copy exists in
   `us-west-2`.
6. (Optional) `modify_snapshot_attribute(..., UserIds=[other_acct])`
   to share with a second account you own.

## Quiz prep

- Snapshots are incremental; the first writes the full volume, the
  rest write only changed blocks.
- A snapshot is recoverable on its own; you do not need the prior
  snapshot in the chain.
- Snapshots are regional. To use a snapshot in another region you
  must call `copy_snapshot`.
- Sharing a snapshot is done with `modify_snapshot_attribute`. The
  recipient gets permission to call `create_volume` from it, not
  read the data directly.

## Further reading

- [Amazon EBS snapshots](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-snapshots.html)
- [Copy an Amazon EBS snapshot](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-copy-snapshot.html)
- [Share an Amazon EBS snapshot](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-modifying-snapshot-permissions.html)
