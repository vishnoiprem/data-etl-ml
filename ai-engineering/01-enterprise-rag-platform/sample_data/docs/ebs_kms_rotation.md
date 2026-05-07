# Runbook: Rotating an EBS Volume KMS Key

## Purpose

This runbook describes the procedure to rotate the AWS KMS key that encrypts
an EBS volume. It applies to volumes encrypted with a Customer Managed Key
(CMK), not the default AWS-managed key.

## Why rotate

- **Compliance** — SOC 2, PCI-DSS, and our internal Information Security
  Standard require CMK rotation at least annually.
- **Compromise response** — if a key is suspected to be compromised, rotate
  immediately and re-encrypt all data encrypted under it.

## Important: EBS does not support in-place key rotation

Unlike S3, EBS does not let you "change" the KMS key on an existing volume.
The KMS rotation procedure for an EBS volume requires creating a new
encrypted volume and copying the data. Plan for downtime or use snapshot-
based replication during a maintenance window.

## Procedure

### Pre-requisites

- IAM permission `kms:CreateGrant`, `ec2:CreateSnapshot`, `ec2:CopySnapshot`,
  `ec2:CreateVolume` on the source account.
- A new KMS CMK (or a freshly rotated CMK material) with a key alias such as
  `alias/ebs-prod-2025q4`.
- A change ticket approved per the Change Management policy.

### Steps

1. **Quiesce I/O** to the volume. For a database, fsync and freeze the
   filesystem (`xfs_freeze`).
2. **Create a snapshot** of the current volume:
   ```
   aws ec2 create-snapshot --volume-id vol-0123456789abcdef \
       --description "pre-rotation snapshot for vol-... 2025-10-15"
   ```
3. **Copy the snapshot** with the new KMS key:
   ```
   aws ec2 copy-snapshot \
       --source-snapshot-id snap-0123 \
       --source-region us-east-1 \
       --destination-region us-east-1 \
       --encrypted \
       --kms-key-id alias/ebs-prod-2025q4
   ```
4. **Create a new volume** from the copied (newly encrypted) snapshot.
5. **Detach** the old volume from the EC2 instance.
6. **Attach** the new volume in the same device path.
7. **Mount** and verify integrity (e.g., `xfs_repair -n`).
8. **Tag** the new volume with `kms-key=ebs-prod-2025q4` and `rotated-at=...`.
9. **Schedule deletion** of the old volume after a 7-day cool-off (in case of
   issues).

### Validation

- Confirm `aws ec2 describe-volumes --volume-id <new>` shows the new KMS key.
- Confirm CloudTrail logged a `CopySnapshot` and `CreateVolume` event with
  the new key.
- Add the rotation event to the SOC 2 evidence locker.

## Rollback

If the application fails on the new volume:
1. Detach the new volume.
2. Re-attach the original volume (kept for 7 days per step 9).
3. Open an incident ticket and root-cause before retrying.

## Frequency

We rotate EBS CMKs annually for production volumes. Dev/staging may rotate
less frequently if the data is non-sensitive.
