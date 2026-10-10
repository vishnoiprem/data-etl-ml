# L31 — ALB Theory + Internet-Facing vs Internal

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 07
> **Duration target:** 12:00
> **Lecture ID:** L31

## Status

Authored.

## Prereqs

- L27–L30 (load balancer intro + NLB).
- L06 (regions, AZs, subnets) — ALB needs at least two subnets in two
  different AZs to be created.

## Key terms

- **Application Load Balancer (ALB)** — a Layer 7 (HTTP/HTTPS) load
  balancer that makes routing decisions based on the content of the
  request (hostname, path, headers, query string), not just the
  destination IP and port.
- **Content-based routing** — choosing a target group based on
  attributes of the HTTP request (URL path, host header, HTTP
  header, query string, source IP). NLB cannot do this because it
  stops at Layer 4.
- **Internet-facing** — the ALB has a public IPv4 (and optional IPv6)
  address in a public subnet. The DNS name returned by AWS resolves
  from the public internet. This is what users hit for a public
  website.
- **Internal** — the ALB has only private IP addresses in private
  subnets. The DNS name is resolvable only from inside the VPC (or
  via VPN / Direct Connect). Internal ALBs are the workhorse of
  multi-tier apps — the web tier talks to the app tier through an
  internal ALB.
- **Listener** — a process on the load balancer that checks for
  connection requests on a specific port and protocol. The default
  listener is what catches everything that no higher-priority rule
  matched.
- **Target group** — a set of targets (EC2 instances, IP addresses,
  or Lambda functions) plus the health check that decides which of
  them are currently healthy enough to receive traffic.

## Lecture

### Why Layer 7?

The Open Systems Interconnection model has seven layers. Layers 1–4
deal with the mechanics of getting a packet from machine A to machine
B (cables, Wi-Fi, IP, TCP, UDP). Layers 5–7 deal with the **content**
of the conversation: TLS handshake, HTTP request, JSON payload,
multipart form, gzip encoding.

An NLB (Section 6, **L29**) is a Layer 4 device. It receives a TCP
SYN, opens a connection to one of its targets, and shuttles bytes
back and forth. It never reads the HTTP request line. That makes NLBs
blazingly fast and able to handle any protocol — but blind to what is
inside the connection.

An ALB is a Layer 7 device. It terminates the TCP connection, parses
the HTTP request (or HTTPS after decryption), and looks at the host
header, the URL path, the query string, the request method, the
source IP, and the standard HTTP headers. **Then** it picks a target
group and opens a new connection to a target.

That extra hop costs a few milliseconds of CPU per request. In
return you get:

- **Host-based routing** — `api.example.com` goes to the API fleet,
  `admin.example.com` goes to the admin fleet, both behind one ALB.
- **Path-based routing** — `/api/*` goes to the API fleet,
  `/static/*` goes to the CDN origin, everything else returns 404.
- **Native TLS termination** — the ALB holds the ACM certificate,
  does the TLS handshake, decrypts the request, and forwards plain
  HTTP to the targets.
- **WebSocket and HTTP/2 support** out of the box.
- **Lambda as a target** — you can put a Lambda function behind a
  target group. The ALB invokes it synchronously and returns the
  response to the client.

### Internet-facing vs internal — pick by the use case

The single biggest design choice for an ALB is the **scheme**:
`internet-facing` or `internal`.

| Scheme        | Subnets                  | DNS name resolves from        | Typical use                                    |
| ------------- | ------------------------ | ----------------------------- | ---------------------------------------------- |
| internet-facing | 2+ public subnets      | Public internet               | Public websites, public APIs, anything user-facing |
| internal      | 2+ private subnets       | Inside the VPC only           | Microservice-to-microservice, app tier, admin tools |

You cannot change the scheme after creation. If you pick wrong, you
delete the ALB and create a new one. There is **no toggle**.

A common production layout has **both**:

1. An **internet-facing** ALB in public subnets — terminates TLS,
   serves the public website.
2. An **internal** ALB in private subnets — sits in front of the
   internal microservice fleet. The web tier (in private subnets)
   talks to the internal ALB; nothing on the public internet can
   reach it.

### ALB vs NLB at a glance

| Property                   | ALB                            | NLB                       |
| -------------------------- | ------------------------------ | ------------------------- |
| OSI layer                  | 7 (HTTP/HTTPS)                 | 4 (TCP/UDP/TLS)           |
| Routing based on           | Host, path, header, query      | IP + port only            |
| TLS termination            | Yes (ACM cert on the ALB)      | No (pass-through)         |
| WebSocket / HTTP/2         | Yes                            | TCP passthrough only      |
| Static IP / Elastic IP     | No (DNS only)                  | Yes                       |
| Lambda targets             | Yes                            | No                        |
| Cross-zone load balancing  | Always on                      | Off by default (paid for) |
| Latency overhead           | ~ ms (TLS + HTTP parse)        | ~ 100 µs                  |
| Throughput                 | Hundreds of thousands of rps   | Millions of rps           |
| Best for                   | HTTP APIs, websites, microservices | Gaming, IoT, financial trading, voice |

Pick the **NLB** when you need raw speed, a static IP, or a non-HTTP
protocol. Pick the **ALB** for almost everything else.

### Subnets, AZs, and the "at least two subnets" rule

AWS provisions one ALB node per Availability Zone that has at least
one enabled subnet. To get high availability, you must specify
**subnets in at least two different AZs** — if you put all your
subnets in one AZ, the ALB will refuse to be created.

In production:

- Pick **two** AZs (e.g. `us-east-1a`, `us-east-1b`) for cost
  discipline.
- Pick **three** AZs when you can afford the third ALB node and
  want headroom for a single-AZ outage.
- Never put both subnets in the same AZ. AWS will warn you at
  creation time and your ALB will not survive an AZ failure.

### What the ALB gives you for free

- **Health checks** against the targets in each target group. An
  unhealthy target is removed from the rotation until it recovers.
- **Connection draining (deregistration delay)** — when a target is
  deregistered, in-flight requests get up to 300 s (configurable) to
  finish before the target is killed. Default is 300 s.
- **Sticky sessions** — cookie-based session affinity (optional).
- **Access logs** — every request written to S3 for analysis.
- **WAF integration** — attach AWS WAF web ACLs in one click.
- **Integration with ECS / EKS** — `service.beta.kubernetes.io/aws-load-balancer-type: alb` is the one annotation that registers an
  ALB target group for you.

## Hands-on

Nothing to do for this lecture. In **L32** we click into the AWS
console and walk through the 4-step ALB creation flow, then in
**L35** we walk through the equivalent boto3 script in
`code/alb_create/alb_create.py`.

## Quiz prep

- What OSI layer does an ALB operate at, and what does that let it
  do that an NLB cannot?
- What is the difference between an internet-facing and an internal
  ALB? Where would you place each in a 3-tier web app?
- Why must an ALB be created with subnets in at least two AZs?
- Name two things you get with ALB that you do not get with NLB.
- What is a target group, and how does the ALB use health checks to
  decide where to send traffic?

## Further reading

- AWS docs — [What is an Application Load Balancer?](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html)
- AWS docs — [Internet-facing vs internal load balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-scheme.html)
- AWS docs — [ALB target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html)
- L29 — NLB theory (the contrast you need)
- L33 — ALB rules (the meat of what makes an ALB an ALB)
