---
id: L25
title: "API Gateway — Overview, API Types, API Endpoint Types"
section: 7
duration: "7:08"
author: "Prem Vishnoi <prem.vishnoi@example.com>"
udemy_id: 25
---

# L25 — API Gateway — Overview, API Types, API Endpoint Types

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 7 — API Gateway Overview
> **Lecture duration target:** 7:08

## Prereqs

- Sections 1–6 of this course. You should be comfortable creating a Lambda
  function and an execution role in the console.
- Basic HTTP knowledge: methods (GET, POST, PUT, DELETE), status codes, and
  headers. If you have used `curl` or Postman even once, you are set.
- A mental model of "client calls backend over the internet." API Gateway
  sits in the middle of that call.

## Key terms

- **API Gateway** — the AWS managed service that receives HTTP/S and
  WebSocket calls and routes them to a backend (Lambda, HTTP endpoint, AWS
  service, or mock).
- **REST API** — the original, feature-rich API type. Supports API keys,
  usage plans, request/response transformations, request validation, and
  per-method throttling.
- **HTTP API** — the newer, lower-latency, lower-cost API type. Optimized
  for proxying to Lambda or HTTP backends with JWT or IAM auth.
- **WebSocket API** — for bidirectional, persistent connections.
- **Edge-optimized endpoint** — fronted by CloudFront; clients hit the
  nearest edge location.
- **Regional endpoint** — served from a single AWS region; not behind
  CloudFront.
- **Private endpoint** — reachable only from inside your VPC, through a
  VPC endpoint.

## Lecture

Amazon API Gateway is the "front door" for any HTTP or WebSocket API you
expose on AWS. In the broadest terms it is a managed, highly-available
reverse proxy that accepts requests from the public internet (or from
inside your VPC), authenticates them, throttles them, transforms them,
and forwards them to a backend. The backend is almost always a Lambda
function in this course, but API Gateway can also call any public HTTP
endpoint, any AWS service through an "AWS" integration, or return a canned
response from a "MOCK" integration.

In the 2026 edition of the AWS console, API Gateway exposes **three API
types** you can create from the home screen. They are not the same product;
they share a name and not much else. Picking the wrong one means rewriting
your infrastructure later, so L25 is dedicated to helping you decide up
front.

### The three API types

1. **REST API** (the original). A regional or edge-optimized API built on
   the older request/response model. It supports everything in the API
   Gateway feature set: request validation, request/response body and
   parameter transformations, API keys, usage plans, per-method throttling,
   canary deployments, and any of the five auth mechanisms (IAM, Cognito
   User Pool, Cognito Identity Pool, Lambda Authorizer, API Key). REST
   APIs are the only type that supports private endpoints. **All five
   lectures in this section describe REST API features.**
2. **HTTP API**. Built on a newer, lighter implementation. Roughly 70%
   cheaper and noticeably lower latency than REST API, but the feature
   surface is intentionally smaller. HTTP APIs support JWT authorizers,
   IAM authorizers, and (since late 2023) API keys through usage plans,
   but they do **not** support request/response transformations, request
   validation, or resource policies with the same flexibility. If your
   API is a thin proxy to Lambda with JWT auth, pick HTTP API.
3. **WebSocket API**. Persistent, bidirectional connections. The client
   opens a connection, sends messages, and the server can push back at
   any time. We will not use WebSocket APIs in this course, but they are
   the right answer for chat, live dashboards, and multiplayer games.

Use Case 2 in section 8 (the S3-backed CRUD API) and the GenAI Bedrock
API in section 10 are both **REST APIs**, because we will need API keys,
usage plans, and (in L29) a private integration. The decision tree below
captures the same logic.

```mermaid
flowchart TD
    A[Need to expose an API on AWS?] --> B{Bidirectional,<br/>persistent connection?}
    B -- Yes --> W[WebSocket API]
    B -- No --> C{What auth model<br/>do you need?}
    C -- Cognito User Pool<br/>or Lambda Authorizer<br/>with request transforms --> R[REST API]
    C -- Lambda Authorizer is fine,<br/>no transforms needed --> D{Private endpoint<br/>or VPC integration?}
    D -- Yes --> R
    D -- No --> E{Need API keys /<br/>usage plans / canary?}
    E -- Yes --> R
    E -- No --> H[HTTP API<br/>(cheaper, lower latency)]
    H -.JWT only.-> H
    R -.REST API is the<br/>default choice.-> R
```

### The three endpoint types

Once you pick the API type, you pick an **endpoint type**. The endpoint
type controls *where* the API's URL resolves to.

- **Edge-optimized**. API Gateway creates a CloudFront distribution in
  front of the API. When a client in Frankfurt calls the API, the request
  lands at the nearest CloudFront edge, which routes back to your regional
  API Gateway endpoint in, say, `us-east-1`. This minimizes the public-
  internet round trip and lets you attach a single ACM certificate at the
  edge for custom domain names. **Edge-optimized is the default for REST
  APIs in the console.** The trade-off is that you cannot put a WAF or
  custom header policy at the regional layer.
- **Regional**. The URL resolves directly to the regional API Gateway
  endpoint. There is no CloudFront in front. This is what you want when
  you are already using CloudFront in front of API Gateway (double-
  dipping with edge-optimized + your own CDN hurts cacheability) or when
  you need the lowest possible regional latency without edge cache hits.
- **Private**. The API has no public DNS at all. It is reachable only
  through a **VPC endpoint** (an interface VPC endpoint powered by
  AWS PrivateLink) from inside a VPC that you authorize in the API's
  resource policy. Private APIs are the topic of L29 and are how you
  build an internal microservice that is never exposed to the public
  internet.

For Use Case 2 in section 8 we will use a **regional** REST API endpoint,
because the clients are EC2 instances and other AWS resources inside our
own account and a single region, so the edge cache of CloudFront adds cost
without helping latency.

### Where API Gateway fits in this course

API Gateway is the missing piece between the Lambda you built in section 2
and the S3/DynamoDB backends in sections 4 and 6. Up to now every Lambda
function has been triggered by an event (S3, EventBridge, console
"Test"). Section 7 begins the second major pattern of the course:
**Lambda as a request/response backend**, invoked by API Gateway over
HTTP. The next two lectures define what an API looks like on the inside
(resources, methods, integrations); L27 explains how you ship and version
it; L28 explains how you secure it; L29 explains how you keep it entirely
private.

## Hands-on

This lecture is conceptual. There is no code to run.

Before L26, open the API Gateway console in a sandbox account and click
"Create API." Note that the console shows three options (REST, HTTP,
WebSocket) and a separate "REST API (private)" option. You do not have
to create one yet; just observe the language the console uses. This will
make the "API type" vocabulary in L26–L29 feel familiar.

## Quiz prep

Before moving on, make sure you can answer:

1. What are the three API types in API Gateway, and what is each one best
   suited for?
2. What is the difference between edge-optimized, regional, and private
   endpoints?
3. Which API type is the only one that supports private endpoints?
4. Why might you choose a regional endpoint over the default edge-
   optimized one for an internal service?
5. For Use Case 2 in section 8, which API type and endpoint type will we
   pick, and why?

## Further reading

- AWS Docs — *Choose between REST APIs and HTTP APIs*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
- AWS Docs — *API Gateway endpoint types*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-endpoint-types.html
- AWS Compute Blog — *Building a serverless WebSocket API* (for context
  on the third API type).
- L30 — *Serverless Enterprise Use Case 2 — Architecture*. This is where
  the API type decision lands in practice.
