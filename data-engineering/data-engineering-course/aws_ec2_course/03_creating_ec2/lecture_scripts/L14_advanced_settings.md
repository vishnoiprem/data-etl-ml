# L14 — Advanced Settings

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 8:00
> **Lecture ID:** L14

## Status

Authored.

## Prereqs

- L09 (the wizard) — Step 7 is "Advanced details".
- L10–L13 (AMI, instance type, network, storage).

## Key terms

- **IAM instance profile** — a container for an IAM role that an
  EC2 instance can assume. The role's temporary credentials are
  exposed at `http://169.254.169.254/latest/meta-data/iam/...` and
  picked up automatically by the AWS CLI / SDKs.
- **User data** — a shell or cloud-init script that runs once as
  `root` the first time the instance boots. (Covered in detail in
  L15.)
- **Shutdown behavior** — what the instance does when you trigger
  an OS shutdown (`shutdown -h now`). Either `stop` (default) or
  `terminate`. The latter is a footgun.
- **Termination protection** — when enabled, the instance
  **cannot** be terminated via the console / API / CLI until
  protection is disabled. Protects against accidental termination
  (and against `terraform destroy`-style accidents).
- **Detailed monitoring** — CloudWatch metrics at **1-minute**
  granularity instead of the default 5-minute. Costs extra per
  instance per month.
- **Tenancy** — `shared` (default), `dedicated` (single-tenant
  hardware), or `host` (you reserve a bare-metal host). Most
  workloads never change this.
- **Placement group** — a logical grouping of instances for
  low-latency (cluster), spread (one per rack), or partition
  (groups for big data) layouts.

## Lecture

Step 7 of the wizard is the "Advanced details" screen. It's a
soup of checkboxes and dropdowns; the eight that matter for 90%
of workloads are below.

### 1. IAM instance profile

What it does: attaches an IAM role to the instance. Anything on
the instance (the AWS CLI, the SSM agent, your app) can then call
AWS APIs **with that role's permissions** without you embedding
credentials.

The two-step setup:

1. Create an IAM role with a trust policy that allows
   `ec2.amazonaws.com` to assume it.
2. Attach the role to the instance at launch time as an
   "instance profile" (`IamInstanceProfile={Arn: ...}`).

This is the **right** way to give an instance access to S3,
DynamoDB, SQS, etc. Don't bake `AWS_ACCESS_KEY_ID` into user
data — that's the wrong way.

For the boto3 demo in L18 we don't attach an instance profile
because the script doesn't need to call any AWS APIs from
inside the instance.

### 2. User data

A cloud-init script that runs once, as `root`, on the first
boot. Covered in detail in L15. The wizard gives you a single
text box; the script you type is base64-encoded by the launch
flow and boto3 does this for you when you pass `UserData=`.

### 3. Shutdown behavior

What happens when the **OS** triggers a shutdown
(`sudo shutdown -h now`, `systemctl poweroff`, clicking "Shut
down" in a Windows instance):

- `stop` (default) — AWS stops the instance; you can start it
  again. EBS volumes are preserved.
- `terminate` — AWS terminates the instance; the root volume is
  deleted (assuming `DeleteOnTermination=True`); everything is
  gone.

**Gotcha:** if you set shutdown behavior to `terminate` and
someone (or a runaway process) issues a shutdown command, your
instance is gone. There is no confirmation. **Leave it as
`stop`** unless you have a deliberate reason to change it.

The boto3 argument is `InstanceInitiatedShutdownBehavior`.

### 4. Termination protection

A boolean (`DisableApiTermination=True/False`) that **blocks
the terminate call** until protection is disabled. The console
shows a confirmation dialog; the API call returns
`OperationNotPermitted` (with a useful error message).

Termination protection does **not** prevent:

- termination triggered by an expiring spot instance interruption
  notice;
- termination triggered by the instance running out of
  instance-credit balance on a `t2` Unlimited mode (it just
  gets throttled, not terminated);
- automatic scale-in from an Auto Scaling group (it does — but
  the ASG explicitly disables termination protection first).

For a production database, **enable it**.

The boto3 argument is `DisableApiTermination`.

### 5. Detailed monitoring

CloudWatch metrics for EC2 come at **5-minute** granularity by
default. Turn on detailed monitoring and you get **1-minute**
granularity. Cost is roughly $3 per instance per month at
1-minute; free at 5-minute.

You want detailed monitoring when:

- you have a fleet of Auto Scaling instances and you need to see
  scale-in/out events clearly;
- you have a workload that spikes faster than 5 minutes
  (transactional databases, real-time APIs);
- you have an alerting workflow that needs to react within
  minutes.

The boto3 argument is `Monitoring={Enabled: True}`.

### 6. Tenancy

- `shared` (default) — your instance runs on hardware shared
  with other AWS customers. Cheapest.
- `dedicated` — your instance runs on single-tenant hardware.
  Useful for compliance (HIPAA, PCI, govcloud) that requires
  physical isolation. Costs extra per hour.
- `host` — you reserve a specific physical server (a
  "Dedicated Host") and launch instances on it. Useful for
  per-socket / per-core software licensing (Windows Server,
  SQL Server) that bills by physical hardware.

The course leaves tenancy at `shared`. Most of your instances
will too.

### 7. Placement group

A logical grouping of instances for **low-latency
networking** (cluster placement) or **failure-isolation**
(spread / partition placement). Used heavily in HPC, big data,
and tightly-coupled ML. The course's launch script does not
use placement groups.

### 8. Credit specification (T-family only)

T-family instances have two credit modes:

- `standard` (default) — when you run out of CPU credits, the
  instance is throttled back to baseline.
- `unlimited` — when you run out of CPU credits, AWS bills you
  for the extra vCPU-hours and lets you burst indefinitely.

Unlimited mode is great when you want T-family prices **and**
occasional spikes. For sustained high-CPU workloads you should
still move to a non-burstable family.

The boto3 argument is `CreditSpecification={CpuCredits:
'unlimited'}`.

### What the wizard shows that doesn't matter

- **"Auto-enable" CloudWatch detailed monitoring** — only
  matters if you've turned detailed monitoring on elsewhere.
- **"T2/T3 unlimited" credit specification** — only for T
  family.
- **Tenancy** — leave at `Shared` unless compliance says
  otherwise.

### How the boto3 demo handles it

The `launch_instance.py` script does **not** set
`DisableApiTermination`, `Monitoring`, or
`InstanceInitiatedShutdownBehavior`. The defaults (termination
protection off, basic monitoring, shutdown = stop) are the right
choice for a learning environment. For a production instance
you'd flip termination protection on in the wizard, or pass
`DisableApiTermination=True` in your boto3 call.

## Quiz prep

- What does the IAM instance profile do? (Attaches an IAM role to
  the instance so the AWS CLI / SDK on the instance can call AWS
  APIs without static credentials.)
- What's the default shutdown behavior? (`stop`.)
- What does termination protection prevent? (Termination via the
  console, API, or CLI — but not spot interruption or ASG
  scale-in.)
- How often does CloudWatch report metrics by default, and what
  does "detailed monitoring" change? (5 minutes by default;
  detailed monitoring = 1 minute, costs extra.)

## Further reading

- AWS docs: *Instance metadata and user data* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html>
- AWS docs: *Instance termination protection* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html#Using_ChangingDisableAPITermination>
- AWS docs: *Burstable performance instances (T2/T3 Unlimited)* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-credits-unlimited-mode.html>
