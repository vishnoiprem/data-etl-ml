# L27 — What is a Load Balancer?

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 06
> **Duration target:** 10:00
> **Lecture ID:** L27

## Status

Authored.

## Prereqs

- L04–L26 (entire course up to here). You should be comfortable with
  EC2 instances, subnets, AZs, security groups, AMIs, and pricing.

## Key terms

- **Load balancer** — a single, stable network endpoint that distributes
  incoming traffic across a pool of backend targets (EC2 instances,
  IP addresses, containers, or Lambda functions).
- **Backend target** — anything that can serve a request: usually an
  EC2 instance, but ALB can target IP addresses and Lambda, and NLB
  can also target static IPs (handy for on-prem boxes).
- **Single point of entry** — the load balancer has one DNS name
  (e.g. `my-nlb-1234.elb.us-east-1.amazonaws.com`) and one or more IP
  addresses; clients always talk to it, never to a specific instance.
- **Internet-facing scheme** — the load balancer has a public IP and
  is reachable from the open internet.
- **Internal scheme** — the load balancer has only private IPs; it is
  reachable only from inside the VPC (or peered networks).

## Lecture

Why do we need a load balancer? The most common reason is the
opposite of what most people guess. A load balancer is not primarily
about "spreading load" — that is a happy side effect. The primary
reason a load balancer exists is to give you a **stable name** that
points at a **changing set of backends**.

Imagine you launch one EC2 instance on Monday, give it an Elastic IP,
and point `www.example.com` at that IP. On Tuesday, the instance
crashes. On Wednesday, you launch a replacement. The IP changes
every time. You have to update DNS, wait for TTLs to expire, and your
users see a brownout in the meantime. A load balancer solves this: the
DNS name of the load balancer is constant, and the load balancer's job
is to know which backends are currently healthy. The instance behind
the load balancer can be replaced any time, and the load balancer's
DNS name never changes.

The second reason is **horizontal scaling**. A single EC2 instance can
only handle so many requests per second — depending on the workload,
that is anywhere from 1k to 50k. If you need to handle more, you add
more instances. The load balancer spreads each new request across
whatever instances are currently healthy. This is the "elastic" in
"elastic load balancing".

The third reason is **failure isolation**. With one instance, any
hardware problem, kernel panic, or deployment error takes the site
down. With a load balancer in front of three or four instances, the
load balancer's health checks will detect a failed instance and stop
routing to it. End users keep getting served by the survivors.

Now let's talk about the **single-AZ vs multi-AZ** decision. A single
load balancer node lives in a single subnet, which lives in a single
Availability Zone. If that AZ has a problem, that one node is in
trouble. AWS therefore always deploys load balancers across **at
least two AZs** (and, in production, you should use three). Each AZ
gets one load-balancer node, and the nodes share one DNS name. If
one AZ goes down, the other AZs keep serving traffic. This is the
load balancer's built-in answer to "what if a datacenter disappears?"

Finally, the **scheme** decision. The scheme is set when you create
the load balancer and it is permanent.

- **Internet-facing**: the load balancer has public IPs. Use it for
  anything that needs to be reachable from outside AWS — public
  websites, public APIs, mobile backends.
- **Internal**: the load balancer has only private IPs, on your VPC's
  internal subnets. Use it for internal microservices, internal
  admin panels, anything that should never be exposed to the public
  internet.

Most beginners start with internet-facing and reach for internal later
when they split their architecture into public and private subnets.
Section 7's ALB lecture revisits the scheme decision in more depth.

## Hands-on

No code in this lecture. Just the mental model.

## Quiz prep

- A load balancer's main job is giving you a **stable name** in front
  of a changing set of backends.
- **Multi-AZ** is the default; single-AZ is a footgun.
- **Internet-facing** = public IPs; **internal** = private IPs only.
- The load balancer's DNS name never changes even if every backend
  instance is replaced.
- A health check is what makes a load balancer more than a glorified
  round-robin DNS record.

## Further reading

- AWS Docs — *What is Elastic Load Balancing?*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html>
- AWS Docs — *Network Load Balancer*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html>
- Diagram: `diagrams/nlb_request_flow.mmd` (sequence diagram of one
  TCP request through an NLB).
