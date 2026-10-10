# L09 — The EC2 Creation Wizard (Overview)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 8:00
> **Lecture ID:** L09

## Status

Authored.

## Prereqs

- L04–L08 (EC2 Fundamentals): you should know what a VM, host,
  hypervisor, AMI, instance type, region, and AZ are.

## Key terms

- **AMI** — Amazon Machine Image. The template that contains the OS,
  applications, and the root volume layout used to boot an instance.
- **Instance type** — the hardware shape (CPU, memory, network,
  storage) the instance runs on, e.g. `t3.micro`.
- **Security group** — a stateful virtual firewall attached to the
  instance's network interface. Controls inbound and outbound traffic.
- **Key pair** — an RSA public/private key pair. AWS stores the public
  key; you store the private key (`*.pem`) on your laptop to SSH in.
- **User data** — a shell or cloud-init script that runs once, as
  `root`, the first time the instance boots.
- **EBS** — Elastic Block Store. Network-attached block storage that
  persists independently of the instance lifecycle.

## Lecture

In L04–L08 we built the **mental model**: a VM is just a process on a
hypervisor that lives in an Availability Zone inside a region. An AMI
is the template. An instance type is the hardware shape. Section 3 is
about turning that mental model into a **single boto3 call that
returns an instance id**.

Before we look at the boto3 call, this lecture is the **map** of the
AWS console's "Launch instance" wizard. The console is the friendliest
way to learn the steps; once you know them, the boto3 call will feel
like a 1:1 translation.

### The 7-step wizard

When you click **Launch instance** in the EC2 console, AWS walks you
through seven screens. Every screen corresponds to a keyword argument
in `ec2.run_instances()`:

1. **Name and tags.** A free-text name plus any number of key/value
   tags. Tags propagate to the instance, its volumes, and its
   network interface. The console always asks for `Name`; the rest
   are optional. In boto3 this is the `TagSpecifications` argument.
2. **Application and OS Images (AMI).** The template. You'll see
   "Quick Start" (Amazon Linux 2, Ubuntu LTS, Windows, macOS, Red
   Hat), "AWS Marketplace" (paid AMIs with pre-installed software),
   and "My AMIs" (your own or community AMIs). In boto3 this is
   `ImageId`.
3. **Instance type.** The hardware shape. `t3.micro` is the free
   tier; `m5.large`, `c5.xlarge`, `r5.4xlarge`, and so on are common
   production shapes. In boto3 this is `InstanceType`.
4. **Key pair (login).** Which RSA public key AWS should inject into
   the instance's `~/.ssh/authorized_keys` (Linux) or how to
   decrypt the Windows admin password. In boto3 this is `KeyName`.
5. **Network settings.** VPC, subnet, public IP, and (optionally)
   security groups. In boto3 these are `SubnetId`, `SecurityGroupIds`,
   and `AssociatePublicIpAddress`.
6. **Configure storage.** The root EBS volume and any additional
   EBS volumes. Volume type (gp3, io2, st1, sc1), size, IOPS,
   throughput, encryption, and `DeleteOnTermination`. In boto3 this
   is the `BlockDeviceMappings` argument.
7. **Advanced details.** IAM instance profile, user data, shutdown
   behavior, termination protection, detailed monitoring, placement
   group, tenancy, and credit specification. In boto3 these map to
   `IamInstanceProfile`, `UserData`, `InstanceInitiatedShutdownBehavior`,
   `DisableApiTermination`, `Monitoring`, etc.

After the seventh step you click **Launch instance**, AWS shows you a
"Launch status" page with the new instance id, and you're done. The
**first time** it takes 5–10 minutes. The **second time** it takes
30–60 seconds.

### Why a wizard?

The wizard exists because the **minimum viable launch** is genuinely
non-trivial: it requires a network (subnet), a firewall (security
group), a credential (key pair), a template (AMI), and a hardware
shape (instance type). AWS chose to make all of those explicit
choices because the consequences of getting them wrong (you've now
exposed a public RDP port to `0.0.0.0/0`) are costly.

### How the wizard maps to boto3

Here's the **at-a-glance translation** we'll use for the rest of the
section:

| Wizard step | boto3 keyword |
|---|---|
| 1. Name & tags | `TagSpecifications=[{ResourceType, Tags}]` |
| 2. AMI | `ImageId` |
| 3. Instance type | `InstanceType` |
| 4. Key pair | `KeyName` |
| 5. Network | `SubnetId`, `SecurityGroupIds`, `AssociatePublicIpAddress` |
| 6. Storage | `BlockDeviceMappings=[{DeviceName, Ebs}]` |
| 7. Advanced | `UserData`, `IamInstanceProfile`, `Monitoring`, `DisableApiTermination`, `InstanceInitiatedShutdownBehavior` |

By the end of L18 you'll be able to read any of those arguments
without thinking.

### The single biggest mistake beginners make

Skipping the **security group** step and letting AWS pick the
"default" security group. The default SG allows **all outbound
traffic** and **no inbound traffic** — so a brand-new instance
launched into the default SG is unreachable from the internet even
if it has a public IP. We'll cover SGs in depth in L17.

### What this lecture intentionally doesn't do

We don't click "Launch" in the console. We just walk through the
screens. The actual hands-on comes in L18, where the boto3 script
does the launch.

## Quiz prep

- How many steps are in the EC2 creation wizard? (7.)
- Which wizard step corresponds to the boto3 `ImageId` argument? (Step
  2, "Application and OS Images (AMI)".)
- Which wizard step corresponds to the boto3 `KeyName` argument? (Step
  4, "Key pair (login)".)
- What's the most common mistake beginners make on the security group
  step? (Leaving the default SG, which blocks all inbound traffic.)

## Further reading

- AWS docs: *Launch your instance* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/LaunchingAndUsingInstances.html>
- AWS docs: *RunInstances API reference* — <https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RunInstances.html>
