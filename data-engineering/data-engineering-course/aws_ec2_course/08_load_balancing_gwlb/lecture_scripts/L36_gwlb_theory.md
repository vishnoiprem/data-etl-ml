# L36 — Gateway Load Balancer (GWLB) Theory

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 08
> **Duration target:** 12:00
> **Lecture ID:** L36

## Status

Authored.

## Prereqs

- L27–L35 (NLB + ALB theory + hands-on).
- L12 — basic VPC / subnet / route-table mental model.

## Key terms

- **Gateway Load Balancer (GWLB)** — Layer-3, transparent appliance
  insertion service. Unlike ALB (L7) and NLB (L4), a GWLB does **not**
  terminate the connection — it transparently forwards flows to a fleet
  of third-party virtual appliances and returns them.
- **GENEVE** — Generic Network Virtualization Encapsulation
  (RFC 8926). A modern tunneling protocol with a flexible metadata
  header, on IANA-assigned **UDP port 6081**. Replaces VXLAN for AWS
  appliance insertion.
- **Transparent inline insertion** — the source and destination IPs of
  the customer flow are preserved end-to-end; the appliance sees the
  real packet, and the source/destination see only each other. The
  appliance is invisible at L3.
- **Appliance vendor / Marketplace** — Palo Alto, Fortinet, Check
  Point, Cisco, F5, etc. sell VM images on AWS Marketplace that you
  register as GWLB target instances.
- **VPC endpoint service** — the production way to expose a GWLB to
  other VPCs (or to on-prem via DX / VPN). Fronted with a Network Load
  Balancer that is then registered as a PrivateLink endpoint service.
- **Flow stickiness (5-tuple hash)** — GWLB hashes on
  src-IP + dst-IP + proto + src-port + dst-port so all packets of a
  single flow land on the same appliance instance for the life of the
  flow.

## Lecture

Welcome to Section 8. We've spent the last nine lectures (L27–L35)
learning how ALB and NLB terminate and re-establish connections. The
Gateway Load Balancer is fundamentally different. **It does not
terminate anything.** It is a Layer-3 transparent insertion service.

Think of GWLB as the AWS-managed version of "patch cable into a
firewall, then patch cable out." In the on-prem world you would
physical-cable your traffic through a rack of firewall appliances.
GWLB gives you the same architectural pattern, but virtualized, with
horizontal scaling, health checks, and cross-AZ failover.

### The protocol — GENEVE on UDP 6081

GENEVE is a small (8-byte fixed) tunneling header that wraps the
**entire original L2 frame** in a UDP datagram on port 6081. AWS chose
GENEVE over VXLAN because GENEVE's variable-length option space lets
appliance vendors carry per-flow metadata — flow IDs, tenant IDs,
policy decisions — alongside the encapsulated packet. The customer
flow inside is unmodified. The src-IP, dst-IP, ports, payload — all
preserved bit-for-bit.

That is what "transparent" means. From the perspective of the EC2
instance sending the traffic, the destination is the real destination
IP. The GWLB is not in the path of the connection; it is in the path
of the packet.

### Why a third LB type?

ALB is great for HTTP. NLB is great for raw TCP/UDP at line rate.
Neither of them lets a third-party firewall inspect the actual
payload while preserving the original source and destination IPs. ALB
becomes the source IP. NLB becomes either the source IP or the
client IP (with proxy-protocol v2) — but it does not let the appliance
*modify* the payload and forward it on, because the connection is
already terminated.

GWLB solves this. It forwards the encapsulated frame to a virtual
appliance, the appliance inspects or rewrites it, then returns the
(now potentially modified) frame to the GWLB which de-encapsulates
and forwards it on to the real destination. The customer workload
sees the original source IP, talks to the original destination IP,
and has no idea the appliance was there.

### The appliance-vendor pattern

In production you don't write the firewall — you buy it from a vendor
(Palo Alto Networks VM-Series, Fortinet FortiGate, Check Point CloudGuard,
Cisco Firepower, F5 BIG-IP, etc.). You subscribe to the listing on
AWS Marketplace, launch the vendor AMI in your VPC, and register the
appliance's ENI as a target in the GWLB target group. The vendor
typically also publishes a CloudFormation template that wires the
appliance + GWLB + VPC endpoint service together for you.

This is why GWLB is a "thin" AWS service. The smarts are in the
appliance; AWS handles the cross-AZ scaling, the GENEVE
encapsulation, the 5-tuple flow stickiness, and the health-check-driven
target rotation.

### Traffic flow

1. Customer EC2 instance sends a packet with dst-IP = some workload in
   a different subnet. The VPC route table has a route for that
   destination whose next-hop is the **GWLB endpoint**.
2. GWLB endpoint receives the packet, **GENEVE-encapsulates** it
   (src-IP = GWLB ENI, dst-IP = appliance ENI, UDP/6081), and
   delivers it to a healthy appliance instance. Flow stickiness via
   5-tuple hash means all packets of this flow hit the same instance.
3. The appliance inspects (and optionally modifies) the inner
   packet, re-encapsulates it, and returns it to the GWLB endpoint.
4. The GWLB endpoint de-encapsulates and forwards the (possibly
   modified) original packet on to the workload's real IP.

### VPC endpoint service pattern

In a real multi-VPC or hybrid deployment you do not consume the GWLB
directly. Instead:

- You put the GWLB in a **service VPC** that runs the appliances.
- You front the GWLB with a **Network Load Balancer**.
- You register the NLB as a **VPC endpoint service** (AWS PrivateLink).
- Consumer VPCs (or on-prem via DX / VPN) create **interface VPC
  endpoints** that point at the endpoint service.

Traffic from the consumer VPC enters via the PrivateLink interface
endpoint, hits the NLB, hits the GWLB, hits the appliance, and back.
The consumer VPC never needs direct VPC peering or transit gateway
routes to the appliance VPC. This is the production deployment
pattern you'll build at deploy time.

### Cross-AZ + health checks

A GWLB is always deployed across exactly **two subnets in two
different AZs**, just like an NLB. The two AZs provide zonal
redundancy: if you lose an AZ, the other AZ's appliances keep
serving flows.

Health checks are HTTP on a port the appliance itself controls
(typically port 80 on the management interface). When an appliance
fails its health check, the GWLB drains it: in-flight flows continue
to be routed to it (so they aren't dropped mid-connection), but new
flows are steered to other healthy appliances.

That is the GWLB in one lecture. Next (L37) we will build one with
boto3.

## Hands-on

L36 is theory only. The hands-on follows in L37.

## Quiz prep

- The GWLB protocol is GENEVE on UDP port 6081.
- A GWLB is always deployed across exactly **two subnets in two AZs**.
- GWLB performs **flow stickiness** using a 5-tuple hash
  (src-IP, dst-IP, proto, src-port, dst-port).
- Health checks for a GWLB target group are typically **HTTP** (the
  appliance exposes a management endpoint, e.g. `/health` on port 80).
- A GWLB does **not** terminate the customer connection — it is
  transparent at Layer 3.
- In production, GWLB is consumed via a VPC Endpoint Service
  (PrivateLink) backed by an NLB that fronts the GWLB.

## Further reading

- AWS Docs — *What is a Gateway Load Balancer?*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/introduction.html>
- RFC 8926 — *Generic Network Virtualization Encapsulation (GENEVE).*
  <https://datatracker.ietf.org/doc/html/rfc8926>
- AWS Blog — *Insert virtual appliances into your VPC flow with Gateway
  Load Balancer.*
  <https://aws.amazon.com/blogs/networking-and-content-delivery/inserting-virtual-appliances-in-your-vpc-flow-with-gateway-load-balancer/>