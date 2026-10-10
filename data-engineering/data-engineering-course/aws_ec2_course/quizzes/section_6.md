# Section 6 Quiz — Load Balancing Intro + NLB

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 6 (L27–L30)
> **Pass bar:** **7 / 10**
> **Time limit:** 15 minutes

## Instructions

- Answer all 10 questions.
- Each question is worth 1 point.
- You need **at least 7 correct** to pass.
- When you are done, check your answers against the answer key at the
  bottom. If you scored below 7, re-read the lecture scripts and
  re-take the quiz.

---

## Questions

**Q1.** What is the primary reason an AWS load balancer exists?

- A. To encrypt traffic in transit.
- B. To provide a stable DNS name in front of a changing set of
  backend instances.
- C. To replace EC2 security groups.
- D. To reduce EC2 pricing.

**Q2.** Which load balancer scheme is reachable from the public
internet?

- A. `internal`
- B. `private`
- C. `internet-facing`
- D. `vpc-only`

**Q3.** In a target group, what is the unit of "which backends are
alive right now"?

- A. The load balancer's DNS name.
- B. The target's health-check state (`initial`, `healthy`,
  `unhealthy`).
- C. The EC2 instance's launch time.
- D. The security group of the target.

**Q4.** A target is `unhealthy`. What does the load balancer do?

- A. Sends 50% of the traffic to it as a penalty.
- B. Stops sending traffic to it.
- C. Terminates the underlying EC2 instance.
- D. Sends traffic to it but flags it in CloudWatch.

**Q5.** Which is the default health-check protocol for an NLB target
group in this course's `nlb_create.py`?

- A. `TCP`
- B. `UDP`
- C. `HTTP`
- D. `ICMP`

**Q6.** An NLB is a **Layer 4** load balancer. What does that mean?

- A. It parses HTTP headers and cookies.
- B. It routes at the transport layer (TCP/UDP/TLS) without parsing
  the HTTP payload.
- C. It only works for IPv4 traffic.
- D. It runs on port 4.

**Q7.** Which feature is unique to the NLB compared to the ALB?

- A. Host-based routing.
- B. Path-based routing.
- C. **Static IP addresses per AZ.**
- D. HTTP/2 support.

**Q8.** You need a load balancer to route `api.example.com` to one
target group and `www.example.com` to a different target group. Which
load balancer do you pick?

- A. NLB
- B. **ALB**
- C. GWLB
- D. Any of the three works.

**Q9.** In boto3, which single client is used to create ALB, NLB,
and GWLB resources?

- A. `boto3.client("elb")`
- B. **`boto3.client("elbv2")`**
- C. `boto3.client("ec2")`
- D. `boto3.client("elb_classic")`

**Q10.** What is the correct order of boto3 calls to set up an NLB
end-to-end?

- A. `create_load_balancer` → `create_target_group` → `create_listener`
- B. **`create_target_group` → `create_load_balancer` → `create_listener`**
- C. `create_listener` → `create_target_group` → `create_load_balancer`
- D. The order does not matter; boto3 resolves dependencies.

---

## Answer key

1. **B** — A stable name in front of a changing set of backends.
2. **C** — `internet-facing`.
3. **B** — The health-check state.
4. **B** — Stops sending traffic.
5. **C** — `HTTP` (intentionally, to read app-level liveness even
   though the listener is TCP).
6. **B** — Layer 4 = transport layer, no HTTP parsing.
7. **C** — Static IPs per AZ. (Host-based / path-based routing and
   HTTP/2 are ALB features.)
8. **B** — ALB; the NLB cannot do host-based routing.
9. **B** — `boto3.client("elbv2")`.
10. **B** — Target group first (it is referenced by the listener),
    then NLB, then listener.
