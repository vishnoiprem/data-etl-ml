# L33 — ALB Rules (host- and path-based)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 07
> **Duration target:** 12:00
> **Lecture ID:** L33

## Status

Authored.

## Prereqs

- L32 (listener created, default action forwards to a target group).
- L27–L28 (target groups, health checks).
- Basic HTTP knowledge (host header, URL path, query string).

## Key terms

- **Rule** — a `(priority, conditions, actions)` triple attached to
  a listener. Evaluated in priority order, lowest first.
- **Condition** — a predicate over the request: host-header,
  path-pattern, http-header, http-request-method, query-string,
  source-ip, or a combination joined by AND.
- **Action** — what to do when the conditions match: forward to a
  target group, redirect to a URL, return a fixed response, or
  (newer) authenticate with OIDC or Cognito.
- **Default action** — the implicit "lowest priority" rule of every
  listener. Runs only when no other rule matched. Every listener
  has exactly one default action.
- **Priority** — a non-negative integer. Rules are evaluated in
  ascending order; the first match wins. Priorities do not have to
  be contiguous, but they must be unique.

## Lecture

A listener with only a default action is just an L4 load balancer
that happens to speak HTTP. The rules you attach to that listener
are what make the load balancer an **Application** Load Balancer.
This lecture is about the anatomy of those rules and the three
patterns that cover 95% of production use.

### Rule anatomy

```
Rule {
  Priority: 10
  Conditions:
    - Field: "path-pattern"
      Values: ["/api/*"]
  Actions:
    - Type: "forward"
      TargetGroupArn: "arn:aws:elasticloadbalancing:...:targetgroup/tg-api/abc123"
}
```

Three pieces:

1. **Priority** — a number. Lower runs first. The default action is
   implicit at the lowest possible priority (think: priority
   infinity). You cannot change the default action's priority.
2. **Conditions** — at least one is required. Multiple conditions on
   the same rule are joined by AND. To get OR, create multiple
   rules.
3. **Actions** — at least one is required. The action types are
   `forward`, `redirect`, `fixed-response`, `authenticate-cognito`,
   and `authenticate-oidc`. The `forward` action is what sends
   traffic to a target group; the others short-circuit the request
   and never touch a target.

### The three patterns you will use

#### Pattern 1 — host-based routing

Use it when **one ALB** should serve **multiple services**, each
with its own DNS name.

```
Rule priority 10:
  IF  host-header is api.example.com OR app.example.com
  DO  forward to tg-api

Default action:
  DO  return fixed 404
```

Production example: a single ALB with one ACM certificate that
covers `*.example.com` routes `api.example.com` to the API
service, `admin.example.com` to the admin service, and returns 404
for everything else. The ALB and the certificate are shared; the
target groups are independent.

#### Pattern 2 — path-based routing

Use it when **one hostname** should serve **multiple services** on
different URL prefixes.

```
Rule priority 10:
  IF  path-pattern is /api/*
  DO  forward to tg-api

Rule priority 20:
  IF  path-pattern is /static/*
  DO  forward to tg-static

Default action:
  DO  forward to tg-default
```

Production example: a single ALB routes `/api/*` to a container
service, `/static/*` to an S3 origin via a small nginx target, and
everything else to a marketing-site target group.

#### Pattern 3 — fixed-response 404 as a default

A surprisingly common and useful pattern: make the **default
action** a fixed response, and only the rules that match get real
traffic. This is what we do in `alb_create.py`.

```
Rule priority 10:
  IF  path-pattern is /api/*
  DO  forward to tg-api

Default action:
  DO  return fixed 404
       Status code: 404
       Content-Type: text/html
       Body: "<h1>Not Found</h1>"
```

Why bother? It surfaces typos in URLs (instead of forwarding them
to a real target and getting a 200 with garbage), it documents the
public surface area in one place, and it is the easiest way to
**decommission a route** without removing the listener.

### Path patterns: what is and is not supported

The `path-pattern` condition is not a full regex. It supports:

- **Exact match** — `/api/v1/users` matches only that URL.
- **Wildcard `*`** — matches zero or more characters within a single
  path segment. `/api/*` matches `/api/v1`, `/api/v2`, `/api/`, but
  **not** `/api/v1/users` (that is two segments).
- **Catch-all `*`** — alone, `*` matches every path.

There is no way to write `/api/**` or `/api/.*` in a path-pattern
condition. If you need true regex routing, you need **two** ALBs
or you need a smarter load balancer in front of the ALB.

> **Trap:** `/api/*` and `/api` are **different patterns**. `/api/*`
> matches `/api/`, `/api/v1`, but not `/api`. If you want both,
> you need two rules or you need to include the `/api` rule
> explicitly.

### Host-header conditions: the `Host:` header nuance

The host-header condition matches the value of the `Host` HTTP
header (case-insensitive). It supports exact match and wildcards:

- `api.example.com` — exact match only.
- `*.example.com` — matches `api.example.com`,
  `admin.example.com`, but **not** `example.com` (the apex).
- `*` — every host.

To host the apex (`example.com`) **and** subdomains on the same
ALB, you must add two rules: one for `example.com` and one for
`*.example.com`.

### Rule order gotcha: priorities do not have to be contiguous

You can leave gaps. The ALB does not care if your priorities are
`10, 20, 30` or `1, 100, 9999`. The temptation to use `1, 2, 3, ...`
is strong; resist it. Leave gaps so you can **insert a new rule
between two existing ones** without renumbering anything.

```
Rule priority 10:  /api/v1/*      → tg-api-v1
Rule priority 50:  /api/v2/*      → tg-api-v2
Default action:                   → 404
```

Need a `/api/v3/*` rule? Insert it at priority 20 or 40. None of
the existing rules change.

### The auth-* actions (overview)

Two newer action types sit **before** your `forward` action and
short-circuit with a redirect to an OIDC or Cognito identity
provider. The pattern is:

```
Rule priority 10:
  IF  path-pattern is /secure/*
  DO  action 1: authenticate-cognito (or authenticate-oidc)
      action 2: forward to tg-secure
```

The ALB handles the entire OAuth2 / OIDC flow: redirect to the IdP,
receive the callback, validate the token, set `X-Amzn-Oidc-*`
headers, and then forward. Your targets just read the headers.

We will not use `authenticate-cognito` in the boto3 script in
**L35** because the `moto` mock does not yet fully support it, but
it is the right tool when you need authentication at the load
balancer layer without writing code.

### What you cannot do with rules

- You cannot use a rule to rewrite the URL path. Use CloudFront or
  nginx if you need that.
- You cannot have **two** `forward` actions in one rule. Use two
  rules if you want a weighted split (`forward` + weight does work
  — see below).
- You cannot run JS or call a Lambda inside a rule. The
  fixed-response and redirect actions are static.
- Cross-region routing is **not** a thing for ALB. Use Route 53
  latency-based routing for that.

### Weighted forwarding

You can have **two** target groups on a single `forward` action
with a weight:

```python
DefaultActions=[{
    "Type": "forward",
    "ForwardConfig": {
        "TargetGroups": [
            {"TargetGroupArn": tg_blue, "Weight": 90},
            {"TargetGroupArn": tg_green, "Weight": 10},
        ],
    },
}]
```

This is the simplest blue/green deploy: 90% to blue, 10% to green.
Bump the weights in 10% steps until you are at 100% green. No
DNS change, no client-side change.

## Hands-on

Add these rules to the ALB you created in **L32**:

1. Priority 10: path-pattern `/api/*` → forward to a second target
   group that has no targets registered yet. (You'll see 503s,
   which is the point — the rule fires but the target group is
   empty.)
2. Default action: fixed response 404 with the body
   `<h1>Not Found</h1>`.

Hit `http://<alb-dns>/` and confirm the 404. Hit
`http://<alb-dns>/api/anything` and confirm the 503 from the
empty target group.

In **L35** we will recreate the same rules in boto3 and assert
them with `moto`.

## Quiz prep

- What are the three parts of an ALB rule, and what is the order
  of evaluation?
- What is the difference between a host-based rule and a path-based
  rule? When would you use each?
- Why would you make the default action a fixed 404 instead of
  forwarding to a real target group?
- What does `/api/*` match? What does it **not** match?
- What is the auth-* action family for, and where in the rule does
  it appear?

## Further reading

- AWS docs — [ALB listener rules](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-rules.html)
- AWS docs — [Rule condition types](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-condition-types.html)
- AWS docs — [Authenticate users using an ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html)
- L31 — ALB theory (where listener rules fit in the mental model)
- L35 — `alb_create.py` walkthrough (rules as code)
