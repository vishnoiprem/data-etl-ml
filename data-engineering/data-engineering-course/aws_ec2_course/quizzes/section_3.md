# Section 3 Quiz — Creating an EC2 Instance

> 12 questions, multi-choice, single answer. Pass bar: **8 / 12**.
> Answers are hidden in collapsible blocks; expand only after
> you've attempted the question.

---

**Q1.** How many steps are in the AWS EC2 "Launch instance" wizard?

- A. 5
- B. 7
- C. 9
- D. 12

<details><summary>Show answer</summary>

**B — 7.** The seven steps are: (1) Name and tags, (2) Application and OS Images (AMI), (3) Instance type, (4) Key pair (login), (5) Network settings, (6) Configure storage, (7) Advanced details.

</details>

---

**Q2.** Which boto3 keyword argument corresponds to the wizard's Step 2 (the AMI)?

- A. `ImageId`
- B. `InstanceType`
- C. `Ami`
- D. `KeyName`

<details><summary>Show answer</summary>

**A — `ImageId`.** boto3 uses `ImageId` to identify the AMI. `InstanceType` is the hardware shape (Step 3), `KeyName` is the SSH key pair (Step 4).

</details>

---

**Q3.** Which Quick Start OS is the recommended default for this course?

- A. Ubuntu Server 24.04 LTS
- B. Windows Server 2022
- C. Amazon Linux 2
- D. macOS Sonoma

<details><summary>Show answer</summary>

**C — Amazon Linux 2.** It's free, AWS-optimized, has the SSM agent and AWS CLI pre-installed, and the `t3.micro` instance is free-tier eligible. Ubuntu and Windows are valid alternatives; macOS is only on specialized host-dedicated instance types.

</details>

---

**Q4.** You're launching a production OLTP database that needs more than 16,000 IOPS and sub-millisecond latency. Which EBS type do you pick?

- A. `gp3`
- B. `st1`
- C. `io2`
- D. `sc1`

<details><summary>Show answer</summary>

**C — `io2`.** `io2` is the Provisioned IOPS SSD, up to 64,000 IOPS per volume with sub-millisecond latency. `gp3` caps at 16,000 IOPS. `st1` and `sc1` are HDDs and are not appropriate for an OLTP database.

</details>

---

**Q5.** What happens if you set **shutdown behavior** to `terminate` and someone runs `sudo shutdown -h now` inside the instance?

- A. The instance stops and can be restarted.
- B. AWS asks for confirmation before terminating.
- C. The instance is terminated immediately, with no confirmation.
- D. The shutdown command is rejected.

<details><summary>Show answer</summary>

**C — The instance is terminated immediately, with no confirmation.** Shutdown behavior = `terminate` means the OS-initiated shutdown path terminates the instance. There is no "are you sure" prompt from AWS. Leave it as `stop` (the default) unless you have a deliberate reason.

</details>

---

**Q6.** Does EC2 user data run on every boot, or only on first boot?

- A. On every boot, including stop/start cycles.
- B. Only on first boot of a fresh instance; not on stop/start.
- C. Once per hour.
- D. Only when triggered manually.

<details><summary>Show answer</summary>

**B — Only on first boot of a fresh instance; not on stop/start.** User data runs once when cloud-init first executes on the instance. If you stop the instance and start it again, user data does not re-run. If you terminate and launch a new instance, the new instance runs user data.

</details>

---

**Q7.** What's the maximum size of the user-data blob?

- A. 1 KB
- B. 16 KB
- C. 64 KB
- D. 1 MB

<details><summary>Show answer</summary>

**B — 16 KB.** That's the published EC2 limit. For bigger artifacts, user data should `curl` from S3 or a similar store rather than embed the content directly.

</details>

---

**Q8.** You launch a new instance and try to SSH in. The instance has a public IP, but the connection times out. What's the **most likely** cause?

- A. The instance's public IP has not propagated to DNS yet.
- B. The security group has no inbound rule allowing port 22.
- C. SSH is disabled by default on Amazon Linux 2.
- D. The instance is in the wrong region.

<details><summary>Show answer</summary>

**B — The security group has no inbound rule allowing port 22.** The default SG has no inbound rules, so all inbound is denied. A "connection timed out" (as opposed to "connection refused") is the classic signature of an SG dropping packets. Add an inbound rule for TCP 22 to fix it.

</details>

---

**Q9.** What is the difference between a public IP and an Elastic IP?

- A. There is no difference; they're the same thing.
- B. A public IP is dynamic and released when the instance stops; an Elastic IP is static and reserved until you release it.
- C. A public IP is free; an Elastic IP costs $1 per month.
- D. A public IP works for IPv4 only; an Elastic IP works for both IPv4 and IPv6.

<details><summary>Show answer</summary>

**B — A public IP is dynamic and released when the instance stops; an Elastic IP is static and reserved until you release it.** Elastic IPs also cost money per hour when they're allocated but not attached to a running instance, so don't allocate them "just in case".

</details>

---

**Q10.** You want your application servers (which all share SG `app-tier`) to be able to reach the database on port 5432. The cleanest way to express the inbound rule on the database's SG is:

- A. Source: `0.0.0.0/0`, port 5432.
- B. Source: the CIDR of the VPC, port 5432.
- C. Source: `sg-xxxx` (the `app-tier` security group id), port 5432.
- D. Source: the database's own security group id, port 5432.

<details><summary>Show answer</summary>

**C — Source: `sg-xxxx` (the `app-tier` security group id), port 5432.** SG-as-source means "any instance attached to this SG can talk to me" — no CIDR maintenance when app servers come and go. Source `0.0.0.0/0` exposes the database to the entire internet (a major security mistake), and self-referential (option D) doesn't help unless the application servers are also attached to the database's SG.

</details>

---

**Q11.** Is a security group **stateful** or **stateless**?

- A. Stateful — if you allow an inbound request, the response is automatically allowed back out, regardless of outbound rules.
- B. Stateless — you must allow both the inbound and outbound sides of every connection explicitly.
- C. It depends on the protocol.
- D. Security groups don't filter traffic; they only tag instances.

<details><summary>Show answer</summary>

**A — Stateful.** If you allow inbound TCP 443, the response is allowed out without an explicit outbound rule. (Compare to a network ACL, which is stateless and evaluates both sides independently.)

</details>

---

**Q12.** What does the boto3 `get_waiter("instance_running")` do?

- A. Polls `describe_instances()` until `State.Name == "running"`, then returns.
- B. Polls `run_instances()` until the API succeeds.
- C. Blocks for 60 seconds, regardless of instance state.
- D. Sends an SNS notification when the instance is running.

<details><summary>Show answer</summary>

**A — Polls `describe_instances()` until `State.Name == "running"`, then returns.** This is why `launch_instance.py` uses the waiter rather than a fixed `time.sleep(...)` — the waiter returns as soon as the instance is actually running, with exponential backoff up to a configurable max.

</details>
