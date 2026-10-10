# L12 — Configuring Network Settings

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 10:00
> **Lecture ID:** L12

## Status

Authored.

## Prereqs

- L06 (Regions and Availability Zones).
- L09 (the wizard) — Step 5 is "Network settings".

## Key terms

- **VPC** — Virtual Private Cloud. A logically isolated virtual
  network in your AWS account. Every EC2 instance lives in a VPC.
- **Subnet** — a range of IP addresses within a VPC, tied to a
  single Availability Zone.
- **Public IP** — an IPv4 address reachable from the public
  internet. Allocated from Amazon's pool, **not** static.
- **Elastic IP** — a static public IPv4 address you own until you
  release it. Costs money when idle.
- **Private IP** — an IP inside your VPC's CIDR. Only routable
  inside the VPC (or via VPN / Direct Connect).
- **Availability Zone placement** — choosing the AZ determines
  which physical data center hosts your instance. Subnets are
  pinned to a single AZ.
- **Internet Gateway (IGW)** — the VPC's door to the public
  internet. Without it, even a public IP is unreachable.
- **Route table** — controls what traffic leaves a subnet. A
  subnet with a default route to the IGW is a "public subnet";
  one without is "private".

## Lecture

Step 5 of the wizard is where many first-time users get confused.
There are four network decisions to make:

1. Which VPC?
2. Which subnet within that VPC?
3. Should the instance get a public IPv4 address?
4. Which security group(s) attach to the instance's ENI?

We'll come back to security groups in L17. This lecture is about
the **placement** decisions: VPC, subnet, AZ, public IP.

### VPC: the outer wrapper

A VPC is a logically isolated virtual network scoped to one AWS
region. By default a new AWS account gets a **default VPC** in
every region, with a `/20` CIDR (about 4,096 addresses), a public
subnet in every AZ, an Internet Gateway, and a route table that
sends `0.0.0.0/0` to the IGW. That default VPC is exactly what you
need to launch a single instance and SSH in from your laptop.

In production you'll typically:

- create a dedicated VPC per environment (`dev`, `staging`,
  `prod`);
- split the VPC into public subnets (for load balancers and
  bastion hosts) and private subnets (for application servers
  and databases);
- peer or share VPCs across accounts using **VPC Peering** or
  **AWS Transit Gateway**.

For section 3 we use the **default VPC** in `us-east-1`.

### Subnet: which AZ?

A subnet is a slice of a VPC's CIDR tied to a single AZ. When you
pick a subnet, you implicitly pick an AZ. Common patterns:

- **Spread across AZs.** A load balancer's target group registers
  instances in `us-east-1a`, `us-east-1b`, and `us-east-1c` so a
  single AZ outage doesn't take down the service.
- **Pin to one AZ.** For very low-latency workloads (e.g. a
  database cluster), you sometimes want all nodes in the same AZ
  to avoid cross-AZ data-transfer charges.

The boto3 `SubnetId` argument takes a single subnet id. If you
want to spread across AZs, you call `run_instances()` multiple
times — once per subnet — or you use an Auto Scaling group with
multiple subnets.

### Public IP: yes or no?

A **public IP** is allocated from Amazon's pool when the instance
launches and **released** when the instance is terminated. (For
instances in a VPC, you can also enable "auto-assign public IP"
at the subnet level.)

If you want a **stable** public IP across stop/start cycles, you
attach an **Elastic IP** — a static address you reserve until you
release it. Elastic IPs cost money when they're not attached to a
running instance, so don't allocate them "just in case".

In the wizard you tick a single checkbox: "Auto-assign Public IP".
In boto3 it's the `NetworkInterfaces[0].AssociatePublicIpAddress`
flag, or — more simply — the top-level `AssociatePublicIpAddress`
argument.

For a course instance you almost always want this on. For a
production database tier you almost always want it off (the DB
should not be reachable from the public internet at all).

### AZ placement: explicit and implicit

Two ways to control which AZ hosts your instance:

- **Implicit** (recommended). Pick a subnet; the instance lands in
  the AZ that subnet belongs to.
- **Explicit** (rare). Set the `AvailabilityZone` argument on
  `run_instances()`. This requires that the subnet you picked is
  in that AZ. We never do this in the course.

### Putting it together for `launch_instance.py`

The launch script takes `--subnet-id` and one or more
`--security-group-ids`. We pass the subnet id rather than the AZ
id because **subnet → AZ is 1:1** and the subnet id is the more
specific thing. We let the boto3 default set
`AssociatePublicIpAddress=False` and explicitly set it to `True`
when the user passes `--associate-public-ip` (left as an exercise
for the reader; the demo script just uses the default).

### Why your "public" instance isn't reachable

Three checks when an instance has a public IP but you can't reach
it:

1. **Subnet is private.** Check the subnet's route table. If
   there's no `0.0.0.0/0 → igw-…` route, the subnet is private.
2. **Security group blocks inbound.** The default SG allows
   outbound and **no inbound** — so a brand-new instance is
   unreachable even if it has a public IP. Add an inbound rule
   for port 22 (SSH) or 80/443 (web).
3. **Network ACL blocks traffic.** NACLs are an additional
   subnet-level firewall; they can override the security group.
   Most default NACLs allow all traffic, but a custom NACL could
   be blocking you.

L17 covers security groups in detail.

### The hidden cost: data transfer

Cross-AZ traffic is **$0.01/GB each direction** (roughly). For
chatty workloads, spreading across AZs adds up. Cross-region
traffic is much more expensive still. Section 3 picks one AZ and
one region; section 6+ (load balancing) revisits this when we
spread across AZs.

## Quiz prep

- What is the difference between a public IP and an Elastic IP?
  (Public IPs are dynamic and released when the instance stops;
  Elastic IPs are static and reserved until you release them — and
  cost money when idle.)
- Is a subnet tied to a single Availability Zone, or to the whole
  region? (One AZ.)
- What's the default behavior of the "default VPC" in a new AWS
  account? (One `/20` VPC per region, with a public subnet in
  every AZ, an IGW, and a default route to the IGW.)
- Name two reasons an instance with a public IP might not be
  reachable. (Subnet is private, security group blocks inbound,
  NACL blocks traffic.)

## Further reading

- AWS docs: *VPCs and subnets* — <https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html>
- AWS docs: *Public IPv4 addresses and external DNS hostnames* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html>
- AWS docs: *Elastic IP addresses* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html>
