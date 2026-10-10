# L29 — Network Load Balancer (NLB)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 06
> **Duration target:** 12:00
> **Lecture ID:** L29

## Status

Authored.

## Prereqs

- L27 (What is a Load Balancer) and L28 (Target Groups and Health
  Checks). This lecture goes deep on the NLB specifically.

## Key terms

- **Layer 4 (L4)** — the transport layer in the OSI model. L4 load
  balancers make routing decisions based on TCP, UDP, or TLS — not on
  the HTTP URL or headers.
- **Static IP per AZ** — each NLB node has one or more **fixed**
  Elastic IPs that do not change for the life of the load balancer.
  This is the NLB's killer feature for allow-listing, DNS A records,
  and firewall rules.
- **Preserve client source IP** — by default, an NLB passes the
  original client IP through to the target, so application logs and
  IP-based authorization still work.
- **Static elasticity** — NLB can handle millions of requests per
  second with very low (~100 µs) latency; suitable for gaming, IoT,
  financial trading, and any other latency-sensitive TCP workload.
- **Connection-based routing** — an NLB routes each TCP connection
  (or UDP flow) to the same target for the life of the connection,
  using a 5-tuple hash (src IP, src port, dst IP, dst port, protocol).

## Lecture

The Network Load Balancer is AWS's **Layer 4** load balancer. It
operates at the transport layer of the OSI model — TCP, UDP, and TLS
— and it makes routing decisions **without ever looking at the HTTP
payload**. It does not parse URLs, headers, or cookies. It does not
do host-based routing or path-based routing. It just opens a TCP
socket from the client, opens a TCP socket to a healthy backend, and
copies bytes between them.

The first consequence of being Layer 4 is **performance**. Because
the NLB does not need to buffer, parse, and re-emit HTTP requests, it
can handle far more traffic per node than an ALB, and with much
lower latency. AWS publishes an NLB capacity of "millions of requests
per second with ~100 µs of additional latency". For most workloads,
the NLB's own latency is small enough that the application's own
processing time is the bottleneck.

The second consequence is **static IPs**. An NLB node has one
Elastic IP per subnet it is deployed in, and those IPs do not change
for the life of the load balancer. This sounds like a small thing.
It is actually huge in practice. It means:

- You can put the NLB's IPs in a corporate firewall allow-list.
- You can point an Apex DNS A record (the bare `example.com`) at the
  NLB. (A CNAME cannot live at the Apex of a DNS zone, so an ALB,
  which has only a DNS name, often cannot.)
- You can put the NLB's IPs in a partner's IP allow-list without
  having to update them every time the load balancer scales.

The third consequence is **preserve client source IP**. By default,
an NLB delivers the original client IP to the backend. The target
EC2 instance sees the real public IP of the caller, not the
private IP of the NLB. This means:

- Application logs are immediately useful (`access.log` shows the
  real client).
- IP-based authorization (`allow 198.51.100.0/24`) works without
  extra configuration.
- You do not need to install the X-Forwarded-For header on the
  application side, because the source IP is already correct.

The fourth consequence — and the one most newcomers miss — is that
the NLB does **not** understand HTTP. It cannot do host-based
routing, path-based routing, sticky sessions by cookie, or HTTP
redirects. If your application needs to serve two domains from one
load balancer, or needs to route `/api/*` to one pool of instances
and `/static/*` to another, you need an ALB, not an NLB. This is the
single biggest reason people switch from NLB to ALB.

Now the decision matrix. **Pick an NLB** when:

- You need raw TCP/UDP/TLS throughput (gaming servers, IoT MQTT,
  financial feeds, syslog).
- You need a static IP per AZ (apex DNS, partner allow-lists,
  on-prem firewall rules).
- You need to preserve the client source IP for security or
  logging.
- You need WebSockets or any long-lived TCP connection where
  connection-level stickiness matters (the NLB routes a TCP
  connection to the same target for its whole life).
- You need extremely low latency (sub-millisecond budgets).
- Your application is non-HTTP (PostgreSQL, Redis, custom binary
  protocol).

**Pick an ALB** when:

- You need host-based or path-based routing.
- You need HTTP-level sticky sessions (cookies).
- You need HTTP/2 or gRPC support.
- You need to terminate HTTPS on the load balancer.
- You need to redirect HTTP to HTTPS at the load balancer layer.

**Pick a GWLB** when:

- You are deploying third-party virtual appliances (firewalls, IDS,
  packet brokers). Section 8 covers this.

For most beginners reading this course, the rule of thumb is: if the
workload is HTTP and you need routing logic, use ALB; if the workload
is anything else (or you need a static IP), use NLB.

The NLB also has a few small but important quirks. First, an NLB only
supports **one TLS listener per port** — you cannot have multiple
TLS certs on the same port like an ALB can. Second, an NLB does
**not** have a security group attached to it; you control access
with the security groups of the **target instances** (and by
choosing `internet-facing` vs `internal`). Third, an NLB's DNS name
resolves to the IP addresses of **all** of its nodes — so if you have
3 AZs, you get 3 IPs, and you can use them for DNS round-robin or
just for resilience.

## Hands-on

No code in this lecture. Just the decision matrix and the static-IP
story.

## Quiz prep

- The NLB is **Layer 4** (TCP/UDP/TLS). It does not parse HTTP.
- An NLB provides **static IPs per AZ** that do not change.
- An NLB **preserves the client source IP** by default.
- An NLB cannot do **host-based or path-based routing** (that is ALB).
- Pick NLB for **non-HTTP, static IP, or extreme throughput**; pick
  ALB for **HTTP routing logic**.
- An NLB does **not** have a security group — control access via the
  targets' security groups.

## Further reading

- AWS Docs — *Network Load Balancer*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html>
- AWS Docs — *Network Load Balancer FAQs*
  <https://aws.amazon.com/elasticloadbalancing/faqs/#Network_Load_Balancer>
- AWS Architecture Blog — *Using static IP addresses for your load
  balancer*
  <https://aws.amazon.com/blogs/networking-and-content-delivery/using-static-ip-addresses-for-application-load-balancers/>
