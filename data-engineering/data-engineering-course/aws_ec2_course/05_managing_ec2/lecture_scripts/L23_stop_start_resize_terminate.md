# L23 — Stop, Start, Resize, Terminate

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 05
> **Duration target:** 12:00
> **Lecture ID:** L23

## Status

Authored.

## Prereqs

- L09–L18 (creating EC2).
- L07 (instance types) — important for the "resize" sub-section.

## Key terms

- **Instance state** — `pending | running | shutting-down | terminated | stopping | stopped`. Six states total; only three (`pending`, `running`, `stopping`/`shutting-down`) are "powered on" in any sense.
- **Stop vs Terminate** — *stop* keeps the EBS root volume and most attributes (private IP, ENI, security groups) intact; *terminate* destroys the instance and (by default) deletes the root EBS volume. Use stop to save money overnight; use terminate when you're done with the workload.
- **Instance resize** — change the instance type without losing the root volume. Requires a stop, a `modify_instance_attribute` (or the console's "Change instance type" action), and a start. You cannot resize while the instance is running.
- **Termination protection** — an instance-level flag (`DisableApiTermination=true`) that blocks `terminate_instances` from the AWS API and the console. It does **not** block stop, reboot, or shutdown from the OS, and it does **not** protect against `DeleteOnTermination` on the volume.
- **EBS-backed vs Instance-store** — the only kind we care about today. An EBS-backed instance survives stop+start; the root volume is detached (not deleted) on stop.

## Lecture

Every EC2 instance moves through a finite state machine. Once you
internalize it, the four operations in this lecture's title — stop,
start, resize, terminate — stop feeling like magic and start feeling
like transitions on a graph.

The six states are `pending`, `running`, `stopping`, `stopped`,
`shutting-down`, and `terminated`. An instance is born in `pending`
(the VM is being allocated on a host), transitions to `running` (the
guest OS has booted), and from there can move to `stopping` (you
asked it to stop) → `stopped`, or to `shutting-down` (you asked it to
terminate) → `terminated`. Once `terminated`, the instance id is
gone forever and the instance cannot be revived. The difference
between `stopping` and `shutting-down` matters in two ways: stopping
is reversible, shutting-down is not; and a stopped instance keeps its
EBS root volume (and its private IP) by default, while a terminated
instance has its root volume deleted if `DeleteOnTermination=true`
(the default for the root volume).

So when do you stop vs. terminate? Stop when the workload is
temporarily not needed (overnight, weekend, a debug session) and you
want to resume without rebuilding. Terminate when the workload is
done. Stopped instances still cost money for the EBS volume they're
sitting on, so "stopped for 6 months" is not free.

Resizing an instance means changing the instance type — `t3.micro`
to `m5.large`, for example. You do this through the console's
"Instance settings → Change instance type" or, programmatically, by
calling `stop_instances`, then `modify_instance_attribute` with the
new `InstanceType`, then `start_instances`. The instance must be
`stopped` for the modification to take effect; you cannot resize
while the instance is running. The root EBS volume and its data
survive the resize. The private IP, the ENI, and the security
groups all survive. What can change: the public IP (if any), the
underlying host hardware, and (sometimes, on Nitro systems) the
instance's MAC address. For most workloads this is invisible.

A few rules of thumb on resizing:

1. You can only resize to a type that is compatible with the
   current AMI's virtualization type. HVM AMIs can launch any modern
   instance type. PV AMIs (very old) cannot.
2. Some resize paths are *not* supported on the underlying host
   without an instance reboot. AWS handles this by doing a soft
   stop / start under the hood when you resize.
3. You cannot downsize an attached EBS volume. To shrink a volume,
   snapshot it, create a new smaller volume from the snapshot, and
   swap the attachments.

Termination protection (`DisableApiTermination=true`) is a safety
net. It is a per-instance flag that prevents the API and console
"Terminate" action from succeeding. It does **not** prevent an OS
shutdown or a `reboot`, and it does **not** prevent
`DeleteOnTermination` on a non-root volume if you set that on the
volume itself. Set termination protection on anything you do not
want to accidentally lose — long-running batch instances, database
hosts, gold-image launchers. Combine it with IAM `Deny` on
`ec2:TerminateInstances` for defense in depth.

## Hands-on

In the AWS console:

1. Launch a `t3.micro` from a recent Amazon Linux 2 AMI.
2. SSH in, write a file to `/home/ec2-user/canary.txt`.
3. Stop the instance. Verify state is `stopped`. Note the private IP.
4. Modify the instance type to `t3.small` (still free-tier-adjacent).
   Start it. Wait until state is `running`.
5. SSH back in. Confirm `canary.txt` is still there and the private
   IP is unchanged.
6. Enable termination protection on the instance.
7. Try to terminate it from the console — the action should be
   disabled.
8. Disable termination protection, then terminate. Confirm the
   instance reaches `terminated`.

## Quiz prep

- The six EC2 instance states and the transitions between them.
- Stop vs terminate: what survives, what is deleted, when to use
  each.
- Resize requires the instance to be `stopped`; you cannot resize a
  `running` instance.
- Termination protection is per-instance and only blocks the
  `terminate_instances` API action — not OS shutdown, not
  `DeleteOnTermination` on the volume.

## Further reading

- [EC2 instance lifecycle](https://docs.aws.amazon.com/AWSEC2/latest/InstanceGuide/ec2-instance-lifecycle.html)
- [Stop and start your instance](https://docs.aws.amazon.com/AWSEC2/latest/InstanceGuide/Stop_Start.html)
- [Resize an instance](https://docs.aws.amazon.com/AWSEC2/latest/InstanceGuide/resize-instance.html)
