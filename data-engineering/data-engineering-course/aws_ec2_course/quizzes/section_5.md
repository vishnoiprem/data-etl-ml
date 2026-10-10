# Section 5 Quiz — Managing EC2 (L23–L26)

> 10 questions, multi-choice, single answer. The answer key is at the
> bottom. Covers L23 (lifecycle), L24 (snapshots), L25 (AMIs), and
> L26 (the `snapshot_ami_demo.py` walkthrough). Pass bar: **7 / 10**.

---

**Q1.** Which EC2 instance states are part of the standard lifecycle?

- A. `pending`, `running`, `paused`, `stopped`, `terminated`
- B. `pending`, `running`, `stopping`, `stopped`, `shutting-down`, `terminated`
- C. `starting`, `running`, `shutting-down`, `deleted`
- D. `pending`, `running`, `sleeping`, `terminated`

---

**Q2.** You stop a running EBS-backed EC2 instance. What happens to the root EBS volume and the instance's private IP?

- A. The root volume is deleted; the private IP is released.
- B. The root volume is preserved and stays attached; the private IP is preserved.
- C. The root volume is preserved but detached; the private IP is released.
- D. The root volume is deleted; the private IP is preserved.

---

**Q3.** You want to change a running instance's type from `t3.micro` to `m5.large`. What is the correct sequence?

- A. `modify_instance_attribute(InstanceType=...)` while running, no restart needed.
- B. Stop the instance, `modify_instance_attribute(InstanceType=...)`, then start the instance.
- C. Terminate the instance and relaunch with the new type.
- D. Reboot the instance — the new type is picked up automatically.

---

**Q4.** You set `DisableApiTermination=true` on an EC2 instance. What is the effect?

- A. The instance can never be stopped, started, or terminated.
- B. The instance cannot be terminated via the `terminate_instances` API or the console. OS-level shutdown / reboot are not blocked.
- C. The instance's root volume is protected from deletion.
- D. The instance becomes immune to all IAM policy denials.

---

**Q5.** Which statement is **true** about EBS snapshots?

- A. Each snapshot is a full, independent copy of the volume — there is no incremental behavior.
- B. Snapshots are incremental at the block level, but the full volume is recoverable from any single snapshot.
- C. Snapshots are incremental at the file level, and you need the chain of snapshots to recover the latest state.
- D. Snapshots are deduplicated across all accounts in the same region.

---

**Q6.** You create a snapshot in `us-east-1` and want to launch an instance from it in `eu-west-1`. What do you do?

- A. Snapshots are global; just `run_instances` in `eu-west-1`.
- B. Call `copy_snapshot(SourceSnapshotId=..., SourceRegion="us-east-1", DestinationRegion="eu-west-1")`, then `run_instances` in `eu-west-1`.
- C. Call `register_image` in `us-east-1` with the cross-region flag.
- D. Modify the snapshot's region attribute to `eu-west-1`.

---

**Q7.** You want to share an EBS snapshot with another AWS account. Which API call do you use, and what does the recipient get?

- A. `grant_snapshot_access` — the recipient gets read access to the snapshot's data.
- B. `modify_snapshot_attribute(Attribute="createVolume", OperationType="add", UserIds=[...])` — the recipient gets permission to call `create_volume` from it.
- C. `create_snapshot_copy_permission` — the recipient gets a full copy in their account.
- D. There is no way to share a snapshot; you must create a new volume in the recipient's account.

---

**Q8.** You call `deregister_image(ImageId=ami-...)` on a custom AMI. What is the effect on the underlying EBS snapshots?

- A. Both the AMI and its snapshots are deleted.
- B. The AMI is removed; the snapshots are left intact and must be deleted separately.
- C. The AMI is marked deprecated; the snapshots are kept for 30 days.
- D. The AMI is removed; the snapshots are automatically moved to Glacier.

---

**Q9.** In `snapshot_ami_demo.py`, what is the purpose of the `BlockDeviceMappings` parameter passed to `register_image`?

- A. It tells AWS which subnet to launch the AMI's instances into.
- B. It lists the volumes to attach at launch, including the snapshot id that backs the root device.
- C. It is required for the IAM policy to be valid.
- D. It is only used for Windows AMIs.

---

**Q10.** The `snapshot_ami_demo.py` script polls `describe_snapshots` and `describe_images` in a loop until the resource reaches a terminal state. Why not use a `time.sleep(60)` instead?

- A. `time.sleep(60)` is not allowed in boto3.
- B. Polling is the textbook way to wait for an async AWS operation, and lets you exit early when the operation finishes; `time.sleep(60)` wastes time when the operation completes in 5 seconds, and can time out when it takes 70.
- C. Polling is required for IAM to work.
- D. boto3 raises a `Boto3TimeoutError` after 30 seconds if you don't poll.

---

# Answer Key

1. **B** — `pending`, `running`, `stopping`, `stopped`, `shutting-down`, `terminated`. `paused` and `sleeping` are not EC2 states.
2. **B** — Stopping an EBS-backed instance keeps the root volume attached and preserves the private IP. The root volume is only deleted on *terminate* (when `DeleteOnTermination=true`, the default for the root volume).
3. **B** — You must stop the instance first, then `modify_instance_attribute` with the new `InstanceType`, then start. You cannot resize a `running` instance.
4. **B** — `DisableApiTermination` only blocks the `terminate_instances` API action and the console's Terminate button. OS shutdown, reboot, and per-volume `DeleteOnTermination` are unaffected.
5. **B** — Snapshots are incremental at the block level, but the full volume is recoverable from any single snapshot. AWS tracks block-level references and assembles the right set of blocks at restore time.
6. **B** — Snapshots are regional. To use a snapshot in another region, call `copy_snapshot` with the source region and destination region. Then you can register an AMI or create a volume in the destination.
7. **B** — `modify_snapshot_attribute(Attribute="createVolume", OperationType="add", UserIds=[...])` grants the recipient account permission to call `create_volume` from the snapshot. They do not get direct read access to the snapshot's data.
8. **B** — `deregister_image` removes only the AMI registration. The underlying snapshots are left intact and must be deleted separately with `delete_snapshot`.
9. **B** — `BlockDeviceMappings` lists the volumes to attach at launch. With one entry, the `Ebs.SnapshotId` is the snapshot the root device is built from — which is exactly the pattern `snapshot_ami_demo.py` uses. (`create_image` is the alternative API; it requires an `InstanceId` and snapshots every attached volume of that instance.)
10. **B** — Polling lets the script exit as soon as the operation completes. A fixed `time.sleep(60)` either wastes time on fast operations or risks a timeout on slow ones. boto3 also ships `get_waiter("snapshot_completed")` and `get_waiter("image_available")` for production use, but the demo uses an explicit poll for portability across `moto` versions.
