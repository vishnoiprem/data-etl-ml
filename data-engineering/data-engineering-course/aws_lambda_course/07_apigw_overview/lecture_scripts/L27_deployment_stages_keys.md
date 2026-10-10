---
id: L27
title: "API Gateway — Deployment, API Stages, API Keys and Usage Plans"
section: 7
duration: "3:24"
author: "Prem Vishnoi <pvishnoi@avilx.com>"
udemy_id: 27
---

# L27 — API Gateway — Deployment, API Stages, API Keys and Usage Plans

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 7 — API Gateway Overview
> **Lecture duration target:** 3:24

## Prereqs

- L25 and L26. You should know what a REST API is, what resources and
  methods are, and what a Lambda proxy integration is.
- L57–L58 — Lambda versions and aliases (in section 11, but conceptually
  parallel to API Gateway stages). If you have not reached section 11
  yet, the short version is: a stage is a *snapshot* of the API, just
  like a Lambda version is a snapshot of the function code.

## Key terms

- **Deployment** — a snapshot of the API's resource tree + methods
  + integrations, frozen at a point in time.
- **Stage** — a named reference to a deployment that clients can call.
  Examples: `dev`, `staging`, `prod`. Each stage gets its own URL.
- **Stage variable** — a per-stage key/value that flows into the
  integration at request time (e.g. a different Lambda alias per
  stage).
- **Canary** — a secondary deployment that receives a configurable
  percentage of traffic, for safe rollouts.
- **API key** — an opaque string a client sends in the `x-api-key`
  header. Identifies the *caller* for metering, not for auth.
- **Usage plan** — a bundle of throttling and quota limits that you
  attach API keys to.
- **Throttling** — a rate cap (e.g. 1000 requests/second, 200 burst).
- **Quota** — a long-term cap (e.g. 1,000,000 requests per month).

## Lecture

So far we have described what an API *is* (a resource tree of methods,
each wired to an integration). Now we need to talk about how you actually
*ship* an API to clients, and how you control who can call it and how
much they can call it.

### Deployment and stage

A REST API in API Gateway has a strict separation between *editable*
and *callable*. You can edit the resource tree, add a method, change an
integration, and none of those changes are visible to clients until you
click "Deploy API." Deploying an API produces a **deployment** — an
immutable snapshot of the resource tree at that moment. You then
attach that deployment to a **stage** with a name (commonly `dev`,
`staging`, `prod`, but the names are arbitrary).

Each stage gets its own URL of the form
`https://{api-id}.execute-api.{region}.amazonaws.com/{stageName}/...`.
That means a single API definition can serve three independent URLs
simultaneously: one per stage, each pointing at a different snapshot
of the API. This is the equivalent of having three environments
without three separate APIs to maintain.

Stage variables let you parameterize the integration per stage. The
classic pattern is to put the Lambda function alias in a stage
variable, so the `dev` stage points at the `dev` alias, `staging` at
`staging`, and `prod` at `prod`. Combined with Lambda aliases
(section 11), this gives you a full Git-branch-style promotion flow
without duplicating API definitions.

### Canary

A canary is a second deployment attached to the same stage. API
Gateway splits traffic between the steady deployment and the canary
according to a percentage you set (e.g. 95% / 5%). You can promote the
canary to 100% once you are confident, or roll it back instantly. A
canary is the safe way to roll out a new integration or backend
behavior; you watch the CloudWatch metrics of the canary for a few
minutes, then push it to 100% or roll it back.

### API keys and usage plans

An **API key** is an alphanumeric string API Gateway issues for you. A
client sends it in the `x-api-key` HTTP header. The key identifies the
caller for *metering* and *quota enforcement* — **an API key is not an
authentication mechanism.** A caller with a valid API key can still
call your API in any way the methods allow, unless you also attach
IAM auth, a Lambda authorizer, or a Cognito authorizer (L28).

A **usage plan** is a bundle of throttling limits (rate + burst) and a
quota (e.g. 1M requests per month) that you attach to one or more API
keys. The pattern is:

1. Create the API.
2. Create a usage plan: "Free tier" — 10 req/s, 20 burst, 100k
   req/month.
3. Create another usage plan: "Pro tier" — 1000 req/s, 2000 burst,
   10M req/month.
4. Create an API key per customer.
5. Attach the key to the appropriate plan.

When the customer exceeds the rate, API Gateway returns
`429 Too Many Requests`. When they exceed the quota, the same. The
client SDK (e.g. the AWS SDK's retry logic) knows how to back off
on 429.

This is exactly the pattern we will implement hands-on in L33–L34
of section 8, for the Use Case 2 CRUD API.

### Why not just use IAM for everything

If you are running a public API for external customers, IAM auth
requires every customer to have an AWS account and a long-term
credentials pair. That is rarely what you want. API keys are the
right answer for "I want to identify a customer and limit how much
they can call me, but I do not want to give them AWS credentials."
For more sophisticated per-user auth, you reach for Cognito
User Pools (L28) or a Lambda Authorizer (L38).

## Hands-on

Conceptual in this lecture. The hands-on for API keys and usage plans
is L33 (theory) and L34 (hands-on) in section 8, where we attach
keys and a plan to the Use Case 2 CRUD API.

If you want to peek ahead: open the API Gateway console, click
"Usage Plans" in the left nav, and click "Create." You will see the
three knobs (throttle rate, throttle burst, quota) that this lecture
just described. You cannot yet create a plan because you have no
deployed API, but the form makes the model concrete.

## Quiz prep

1. What is a *stage*, and how is it different from a *deployment*?
2. What is a canary, and what is it useful for?
3. Is an API key an authentication mechanism? Why or why not?
4. What is the difference between throttling and a quota?
5. How would you implement a "free tier" and a "pro tier" for the
   same API using usage plans?

## Further reading

- AWS Docs — *Set up stages for a REST API*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-deploy-api.html
- AWS Docs — *Canary release deployments*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/canary-release.html
- AWS Docs — *Create and use usage plans*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html
- L33–L34 (section 8) — the hands-on of API keys + usage plans.
