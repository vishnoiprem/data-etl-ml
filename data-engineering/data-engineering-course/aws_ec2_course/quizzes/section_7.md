# Section 7 Quiz — Application Load Balancer (ALB)

> 10 questions, multi-choice, single answer. Pass bar **7 / 10**.
> Answers are hidden in collapsible blocks; expand only after you
> have attempted the question.

---

**Q1.** At which OSI layer does an Application Load Balancer make its routing decision?

- A. Layer 2 (data link)
- B. Layer 4 (transport)
- C. Layer 7 (application)
- D. Layer 3 (network)

<details><summary>Show answer</summary>

**C — Layer 7.** An ALB terminates the TCP connection, parses the
HTTP request, and routes by host, path, headers, or query string.
Layer 4 (NLB) only sees IP and port.

</details>

---

**Q2.** You are designing a 3-tier web app: public web tier, private app tier, private data tier. Where should the ALB sit, and what scheme should it have?

- A. One internet-facing ALB in front of the data tier
- B. One internet-facing ALB in front of the web tier, plus an internal ALB in front of the app tier
- C. One internal ALB in front of the web tier
- D. No ALB is needed; the web tier talks directly to the data tier

<details><summary>Show answer</summary>

**B — One internet-facing ALB in front of the web tier, plus an
internal ALB in front of the app tier.** The internet-facing ALB
serves public traffic; the internal ALB lets the web tier reach
the app tier without exposing it to the public internet.

</details>

---

**Q3.** What is the minimum number of subnets an ALB must span, and why?

- A. One subnet; subnets are for routing, not for AZ placement
- B. Two subnets in two different AZs; the ALB needs to survive an AZ failure
- C. Three subnets in three AZs; AWS refuses fewer
- D. Two subnets in the same AZ; AZ boundaries are enforced at the VPC level

<details><summary>Show answer</summary>

**B — Two subnets in two different AZs.** If you specify subnets in
only one AZ, AWS refuses to create the ALB. Spanning two AZs is the
minimum to survive a single-AZ outage.

</details>

---

**Q4.** Which of the following is the **default action** of a listener in AWS?

- A. The first rule with the lowest priority
- B. The action that runs when no other rule matches the request
- C. The action that runs for HTTPS only
- D. The action that runs for every request, regardless of rules

<details><summary>Show answer</summary>

**B — The action that runs when no other rule matches the request.**
Every listener has exactly one default action. It is the fallback
after all higher-priority rules have been evaluated and missed.

</details>

---

**Q5.** Which path-pattern matches the URL `/api/v1/users`?

- A. `/api/*`
- B. `/api/v1/*`
- C. Both A and B
- D. Neither A nor B

<details><summary>Show answer</summary>

**B — `/api/v1/*`.** The `*` in a path-pattern matches within a
single path segment, not across segments. `/api/*` matches `/api/`
and `/api/v1`, but **not** `/api/v1/users`. `/api/v1/*` matches
`/api/v1/users` because everything after `/api/v1/` is within one
trailing segment.

</details>

---

**Q6.** You create an ALB with `Scheme='internal'`. Can you later change it to `Scheme='internet-facing'` without recreating the ALB?

- A. Yes, via the console toggle
- B. Yes, via `modify_load_balancer_attributes`
- C. No; you must delete the ALB and create a new one
- D. Only if the ALB has no listeners

<details><summary>Show answer</summary>

**C — No; you must delete the ALB and create a new one.** The
scheme is fixed at creation time. There is no `modify_load_balancer`
call that changes it, and the console has no toggle.

</details>

---

**Q7.** What is the default cross-zone load balancing setting for an ALB?

- A. Off by default; can be enabled
- B. On by default; can be disabled
- C. Always on; not user-configurable
- D. Cross-zone load balancing does not exist for ALB

<details><summary>Show answer</summary>

**C — Always on; not user-configurable.** For NLB the default is
off and enabling it costs ~$18/AZ/month. For ALB it is free and
there is no setting to change.

</details>

---

**Q8.** An ALB returns 503 to a client. Which of the following is the most likely cause?

- A. The client's TLS certificate is invalid
- B. The target group's listener has no rule that matches the URL
- C. The selected target group has no healthy targets
- D. The ALB's security group is missing an inbound rule

<details><summary>Show answer</summary>

**C — The selected target group has no healthy targets.** 503 from
an ALB almost always means "I tried to forward to a target group
and there was no healthy target to send to." A 502 means the target
received the request but failed; a 404 from a fixed-response rule
is what you get when no rule matched.

</details>

---

**Q9.** Which `elbv2.create_rule(...)` call correctly adds a path-based rule at priority 10 that forwards `/api/*` to a target group?

- A. `create_rule(ListenerArn=l, Priority=10, Conditions=[{"Field": "path-pattern", "Values": ["/api/*"]}], Actions=[{"Type": "forward", "TargetGroupArn": t}])`
- B. `create_rule(ListenerArn=l, Conditions=[{"Field": "path", "Value": "/api/*"}], Actions=[{"Type": "forward", "TargetGroupArn": t}])`
- C. `create_rule(ListenerArn=l, Priority=10, PathPattern="/api/*", TargetGroupArn=t)`
- D. `create_listener_rule(ListenerArn=l, Priority=10, PathPattern="/api/*", TargetGroupArn=t)`

<details><summary>Show answer</summary>

**A.** `Conditions` is a list of dicts with `Field` and `Values`
keys, `Actions` is a list of dicts with a `Type` and a
type-specific config, and `Priority` is a string-of-int passed as
a top-level keyword. Options B, C, and D use incorrect field
names or non-existent methods.

</details>

---

**Q10.** Which boto3 call sets the **default action** of a listener to a fixed 404 response?

- A. `create_listener(..., DefaultActions=[{"Type": "fixed-response", "FixedResponseConfig": {"StatusCode": "404", "ContentType": "text/html", "MessageBody": "<h1>Not Found</h1>"}}])`
- B. `create_listener(..., DefaultAction={"Type": "return-404"})`
- C. `add_listener_rule(..., Action="404", Body="<h1>Not Found</h1>")`
- D. `modify_listener(..., DefaultAction="404")`

<details><summary>Show answer</summary>

**A.** The `DefaultActions` parameter is a **list** of action
dicts. A `fixed-response` action needs a `FixedResponseConfig`
with `StatusCode`, optional `ContentType`, and optional
`MessageBody`. The other options use non-existent parameters or
methods.

</details>