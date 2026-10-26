# L05 — Managed vs Unmanaged Services (and where EC2 fits)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 02
> **Duration target:** 8:00
> **Lecture ID:** L05

## Status

Authored.

## Prereqs

- L04 (VMs, hosts, hypervisors).

## Key terms

- **Managed service** — a service where the cloud provider takes
  responsibility for one or more layers of the stack (hardware,
  operating system, runtime, scaling, patching) so you do not have
  to. The more the provider does, the more "managed" the service is.
- **Unmanaged service** — a service where you are responsible for
  most or all of those layers yourself. EC2 is the canonical example.
- **IaaS (Infrastructure as a Service)** — the cloud service model
  where the provider gives you virtual hardware and you do
  everything above the hypervisor. EC2 is IaaS.
- **PaaS (Platform as a Service)** — the provider also gives you a
  runtime and often a framework. Elastic Beanstalk and Heroku are
  PaaS.
- **SaaS (Software as a Service)** — you just log in. Gmail, GitHub,
  Salesforce.
- **Serverless / FaaS (Function as a Service)** — the provider owns
  the entire stack down to the application process; you upload code
  or a container image. Lambda is the AWS FaaS offering.
- **Shared responsibility model** — AWS's division of "who does
  what": AWS secures the cloud (hardware, hypervisor, data center
  physical security), you secure what you put *in* the cloud (the
  OS, the application, the data, the IAM policies, the security
  group rules).

## Lecture

The single most important thing to know about EC2 is that it is
**not** a managed service. That surprises people — they assume that
because it is on AWS, AWS is doing the patching, the scaling, the
failover, all of it. AWS is doing some of those things. AWS is *not*
doing most of them. The VM you launch is yours to operate.

Let me make this concrete with a definition. A **managed service**
is one where the cloud provider takes responsibility for one or more
layers of the stack — hardware, operating system, runtime, scaling,
patching, backups, security — so you do not have to. The more of
those layers the provider takes on, the more managed the service is.

Where does EC2 sit on that scale? Pretty far toward the
"unmanaged" end. AWS gives you:

- The physical server
- The hypervisor
- The data center (power, cooling, physical security)
- A virtual network with VPC primitives (subnets, route tables,
  NAT, internet gateways)
- EBS volumes (managed block storage, redundant, snapshotable)
- A choice of Amazon Machine Images (AMIs) with the OS pre-installed

What AWS does **not** do for you on EC2:

- Patch the guest operating system
- Install or update the packages on the VM
- Restart the VM if it crashes
- Scale out (add more instances) when load increases
- Scale in (remove instances) when load drops
- Replace the instance if the underlying hardware fails (you have
  to detect that and recover)
- Back up the application data (you have to take EBS snapshots)
- Rotate the SSH key pair
- Update the security group rules
- Apply OS-level security baselines (CIS benchmarks, etc.)
- Monitor the application

That list is not a complaint — it is the trade. You give up the
managed-service convenience and you get **control**. You can run
any operating system, install any software, listen on any port,
mount any filesystem, run any kernel module, use any monitoring
agent, and you can run as root. You cannot do any of those things
in Lambda.

This is why EC2 is classified as **IaaS** (Infrastructure as a
Service). The provider gives you virtual infrastructure and you
do the platform-and-application work on top. If you want EC2 to
behave more like a managed service, you stack additional AWS
services on top: Auto Scaling Groups for scaling, Elastic Load
Balancing for traffic distribution, CloudWatch for monitoring,
Systems Manager for patching, AWS Backup for snapshots, and so on.
Each of those is a separate managed service that *makes EC2 more
manageable* — but EC2 itself is still the raw substrate.

The shared responsibility model captures this neatly. AWS is
responsible for **security *of* the cloud** — the physical
infrastructure, the hardware, the software that runs the EC2
service itself. You are responsible for **security *in* the
cloud** — the guest OS, the security groups, the network ACLs,
the IAM roles attached to the instance, the data on the EBS
volumes, the application, and the credentials the application
uses. When an EC2 instance gets compromised because it had a
public IP and an open SSH port and a weak password, that is on
the customer, not on AWS.

The contrast with Lambda is sharp on purpose. Lambda is a fully
managed, serverless, FaaS offering: AWS owns the hardware, the
hypervisor, the operating system, the runtime, the scaling, the
fault tolerance, and the patching. You upload a function and
that's it. The trade is that you give up the control EC2 gives
you — no custom runtimes without layers, no execution longer than
15 minutes, no choice of instance size, no choice of network
configuration, no persistent local filesystem. Different tool,
different job.

Knowing where EC2 sits on this spectrum is what lets you make
good architectural choices. If you need a long-running
stateful server with full control of the OS — EC2 (or ECS on
EC2, or EKS on EC2). If you need a short stateless job that
runs in response to an event — Lambda. If you need a managed
relational database — RDS, not EC2 with MySQL you installed
yourself. EC2 is the escape hatch — when nothing else fits,
EC2 fits.

## Hands-on

Theory lecture — but take a moment in the EC2 console to
internalize the responsibility split:

1. Go to **EC2 → Instances → select an instance → Security**.
   Read the security group rules. *You* defined those. AWS did
   not pick them for you. If port 22 is open to `0.0.0.0/0`,
   that is a decision you (or whoever set up the account) made.
2. Go to **EC2 → Instances → Monitoring**. The default graphs
   show CPU, network, and status checks. Note: there are no
   application-level metrics here. *You* have to install the
   CloudWatch agent to push memory, disk, and process metrics.

## Quiz prep

- Define "managed service" and "unmanaged service" in your own
  words. Where does EC2 sit on the spectrum?
- List three things AWS does *not* do for you on an EC2 instance.
- What is the shared responsibility model, and what is the
  customer's half for EC2?
- Name the AWS managed services that make EC2 "more managed"
  (Auto Scaling, ELB, CloudWatch, SSM, AWS Backup, ...).
- How does EC2's responsibility model differ from Lambda's?

## Further reading

- AWS: [Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)
- AWS: [AWS Compute Services Comparison](https://aws.amazon.com/products/compute/)
- AWS: [What is Amazon EC2?](https://docs.aws.amazon.com/ec2/)