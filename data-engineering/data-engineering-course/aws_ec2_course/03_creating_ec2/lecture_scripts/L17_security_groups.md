# L17 — Security Groups

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 12:00
> **Lecture ID:** L17

## Status

Authored.

## Prereqs

- L12 (Network Settings) — security groups are part of the
  network tab.
- L09 (the wizard) — Step 5 is "Network settings", which
  includes "Security groups".

## Key terms

- **Security group (SG)** — a stateful virtual firewall attached
  to an ENI (Elastic Network Interface). Controls inbound and
  outbound traffic at the instance level.
- **Stateful** — if you allow an inbound request, the response is
  automatically allowed back out, regardless of outbound rules.
  (Compare: a network ACL, which is **stateless**.)
- **Inbound rule** — allows traffic **into** the instance,
  matching a protocol, port range, and source.
- **Outbound rule** — allows traffic **out of** the instance,
  matching a protocol, port range, and destination.
- **Default SG** — the SG that AWS auto-attaches when you don't
  specify one. Allows all outbound; allows no inbound.
- **Source** — for inbound rules, the "where is this traffic
  coming from?" field. Can be a CIDR (`203.0.113.0/24`) or the
  **id of another security group** (`sg-0123…`).
- **Self-referential rule** — an inbound rule that allows traffic
  from instances in the same SG. The default SG has this for
  itself.

## Lecture

A security group is the single most important security primitive
on EC2. Get it right and your instance is reachable from the
people who need it, and only those people. Get it wrong and you've
exposed your instance to the entire internet — or, just as bad,
locked yourself out.

### Stateful vs stateless

The single most important thing to remember about a security
group is that it is **stateful**. That means:

- If you allow inbound TCP 443 from `0.0.0.0/0`, a request that
  comes in on 443 is allowed, and the **response** is allowed
  back out **without** an outbound rule.
- You do **not** need to "open both sides" of a connection.
- Compare to a network ACL (NACL), which is **stateless** — it
  evaluates inbound and outbound rules independently.

This is great for ergonomics (you write half the rules) and
terrible for understanding the full traffic flow, because half of
the security group story is "what the SG remembers about
established connections".

### Inbound vs outbound rules

Every SG has two rule tables:

- **Inbound rules** — what traffic can come **into** the
  instance.
- **Outbound rules** — what traffic can leave **the instance**.

The default SG has:

- Inbound: **none** (zero rules; all inbound is denied by
  default).
- Outbound: **all** (one rule: `0.0.0.0/0` for all protocols).

That asymmetry catches a lot of beginners: a brand-new instance
attached to the default SG can **talk out** (so `yum update`
works) but **nothing can come in** (so you can't SSH in until you
add an inbound rule).

### The default-deny posture

The actual rule for inbound is "deny everything unless there's
a rule that explicitly allows it." This is the same default-deny
posture as a Linux `iptables` policy of `DROP` on input. Add
rules **only** for the traffic you actually want.

Common rules to add:

| Port | Protocol | When you need it |
|---|---|---|
| 22 | SSH | When you want to SSH in from the public internet. |
| 80 | HTTP | When you serve plain HTTP (e.g. a redirector to 443). |
| 443 | HTTPS | When you serve HTTPS. |
| 3389 | RDP | When you RDP into a Windows instance. |
| 5432 | PostgreSQL | When you accept database connections — but **only from app servers**, not from `0.0.0.0/0`. |

### Source: CIDR vs security group id

For each inbound rule, the **source** field can be either:

- A **CIDR block** (`203.0.113.4/32`, `0.0.0.0/0`,
  `10.0.0.0/16`). Traffic from those IPs is allowed.
- The **id of another security group**
  (`sg-0123456789abcdef0`). Traffic from any ENI attached to
  that SG is allowed.

The second form is the right answer for **internal** traffic
(e.g. "let my application servers reach the database on
5432"). You don't want to maintain a CIDR list of every app
server's private IP — you want to say "any instance tagged
`role=app` can talk to the database." The "any instance with
SG X" abstraction is how you express that without enumerating
IPs.

A self-referential rule is the special case of "let instances in
this SG talk to other instances in this SG". The default SG has
this for itself.

### The most common SGs in a real environment

| SG | Inbound rules | Outbound rules | Used by |
|---|---|---|---|
| `web-tier` | 80/443 from `0.0.0.0/0` | All | Public-facing load balancers and web servers. |
| `app-tier` | 80/443 from `web-tier` SG | All | Application servers. |
| `db-tier` | 5432 from `app-tier` SG | All | Databases. |
| `bastion` | 22 from your office CIDR | All | The single SSH entry-point. |
| `default` | (none) | All | Backstop for any instance that doesn't have a specific SG. |

Notice the layering: `db-tier` allows inbound from the `app-tier`
**security group**, not from a CIDR. New app servers come and go;
you don't have to update the db-tier SG every time.

### What an SG is NOT

- **Not a subnet-level firewall.** That's a network ACL (NACL).
  NACLs are stateless; SGs are stateful. Both can apply to the
  same traffic.
- **Not a replacement for a WAF.** SGs are L3/L4 only — they
  match IP, port, and protocol. They don't understand HTTP
  paths, headers, or query strings. For L7 protection you need
  AWS WAF in front of an ALB.
- **Not a substitute for OS-level firewalls.** SGs filter
  traffic before it hits the network interface. On the
  instance, `iptables` / `nftables` / Windows Firewall can add
  another layer.

### Common mistakes

1. **Source `0.0.0.0/0` on port 22 (SSH).** This is the single
   most common security mistake in EC2. SSH from any IP, with
   the default `ec2-user` user and a key pair, means anyone with
   the private key can log in. Worse: the instance is now
   constantly brute-forced by botnets. **Source your SSH
   rule from your office IP** (`203.0.113.4/32`) or use SSM
   Session Manager.
2. **Source `0.0.0.0/0` on a database port.** Same mistake,
   bigger blast radius. The database is reachable from the
   entire internet; a single misconfiguration gives anyone
   `psql` access.
3. **Forgetting to add an inbound rule at all.** The default
   SG denies all inbound. You'll SSH in and see "connection
   refused" — that's the SG, not the SSH daemon.
4. **Modifying the default SG in a way that affects every
   instance attached to it.** The default SG is the **default**.
   Many instances may be attached. Edit it carefully, or
   create a dedicated SG per workload.

### SGs in boto3

```python
client.run_instances(
    ImageId=ami_id,
    InstanceType="t3.micro",
    SecurityGroupIds=["sg-0123456789abcdef0"],  # <-- list of SG ids
    # ...
)
```

You can also pass a list of SG names with `SecurityGroups=...`
(default-VPC only). The `launch_instance.py` script takes
`--security-group-ids sg-abc123 sg-def456`.

To inspect or modify an SG:

```python
sg = client.describe_security_groups(GroupIds=["sg-abc123"])
print(sg["SecurityGroups"][0]["IpPermissions"])  # inbound
print(sg["SecurityGroups"][0]["IpPermissionsEgress"])  # outbound
```

To add an inbound rule programmatically:

```python
client.authorize_security_group_ingress(
    GroupId="sg-abc123",
    IpPermissions=[
        {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "203.0.113.4/32", "Description": "office"}],
        }
    ],
)
```

### SGs and moto

`@mock_aws` supports `create_security_group`,
`authorize_security_group_ingress`, and `describe_security_groups`
for the EC2 namespace. The launch_instance tests use it to
create a real SG in the mocked environment and attach it to the
instance.

## Quiz prep

- Is a security group stateful or stateless? (Stateful.)
- What's the default behavior of the default security group for
  inbound? outbound? (No inbound; all outbound.)
- Name two advantages of using a security group id as the source
  of an inbound rule, instead of a CIDR. (No CIDR maintenance
  when instances come and go; a clean abstraction of "instances
  with this role can talk to me".)
- What's the most common mistake beginners make with SGs? (Source
  `0.0.0.0/0` on port 22 — SSH from the entire internet.)

## Further reading

- AWS docs: *Security groups for your VPC* — <https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html>
- AWS docs: *Control traffic to your AWS resources using security groups* — <https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html#VPCSecurityGroups>
- AWS docs: *Differences between security groups and network ACLs* — <https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Security.html#VPC_Security_Comparison>
