# Section 7 Quiz — API Gateway Overview

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 7 — L25 through L29
> **10 questions.** Answers are in collapsible blocks immediately after
> each question. Click "Show answer" to reveal.

---

### Q1

What are the three API types supported by Amazon API Gateway, and what
is each one best suited for?

<details>
<summary>Show answer</summary>

- **REST API** — the original, feature-rich API type. Supports API
  keys, usage plans, request/response transformations, request
  validation, canary deployments, and all five auth mechanisms
  (IAM, Cognito User Pool, Cognito Identity Pool, Lambda
  Authorizer, API Key). Also the only API type that supports
  private endpoints. **Best for:** feature-rich APIs that need
  usage plans, transforms, or private endpoints.
- **HTTP API** — the newer, lower-latency, lower-cost type.
  ~70% cheaper than REST API. Supports JWT authorizers, IAM
  authorizers, and (since late 2023) API keys. No request/response
  transformations, no request validation, no private endpoints.
  **Best for:** simple Lambda or HTTP proxies with JWT auth where
  cost and latency matter.
- **WebSocket API** — persistent, bidirectional connections.
  **Best for:** chat, live dashboards, multiplayer games, any
  pattern where the server needs to push to the client.

</details>

---

### Q2

What are the three endpoint types in API Gateway, and how do they
differ?

<details>
<summary>Show answer</summary>

- **Edge-optimized** — fronted by CloudFront. Clients hit the
  nearest edge location, which routes to the regional API Gateway
  endpoint. Best for global public APIs that benefit from edge
  caching. The default for REST APIs in the console.
- **Regional** — the URL resolves directly to the regional API
  Gateway endpoint, with no CloudFront in front. Best when you are
  already using CloudFront separately, or for internal/regional
  APIs where edge caching adds cost without helping latency.
- **Private** — the API has no public DNS. Reachable only through
  an interface VPC endpoint (PrivateLink) from inside an
  authorized VPC. Best for internal microservice APIs that must
  never be exposed to the public internet.

</details>

---

### Q3

Which API type supports private endpoints?

<details>
<summary>Show answer</summary>

Only the **REST API** type supports private endpoints. HTTP APIs and
WebSocket APIs do not.

</details>

---

### Q4

A client sends a request with `x-api-key: abc123` header. Which
authentication mechanism is at work, and is the client *authenticated*?

<details>
<summary>Show answer</summary>

The mechanism is **API Key**. The client is **identified** (so
API Gateway can look up the key, find the attached usage plan, and
enforce throttling/quota), but the client is **not authenticated**.
API Gateway does not check who the client is — only that the key
exists and is attached to a plan. The same person (or someone who
stole the key) could be calling. If you need to know *who* the
caller is, you need IAM auth, Cognito, or a Lambda Authorizer
*in addition to* (or instead of) the API key.

</details>

---

### Q5

What is the difference between a *resource* and a *method* in API
Gateway?

<details>
<summary>Show answer</summary>

- A **resource** is a path in the API, e.g. `/items` or
  `/items/{id}`. Resources form a **resource tree** rooted at `/`.
- A **method** is the HTTP verb attached to a resource, e.g.
  `GET /items`, `POST /items`, `DELETE /items/{id}`. Each method
  is configured independently (auth, validation, integration,
  throttling).

In short: a resource is the *URI*, a method is the *action* on
that URI.

</details>

---

### Q6

What is the **Lambda proxy integration** (`AWS_PROXY`), and why is
it the most common integration type for Lambda-backed APIs?

<details>
<summary>Show answer</summary>

The Lambda proxy integration is the "passthrough" mode where API
Gateway hands the Lambda function a structured event JSON
containing the full HTTP request — path, method, headers, query
string, path parameters, body — and the Lambda function returns a
response JSON in a specific shape (statusCode, headers, body) that
API Gateway uses to build the actual HTTP response.

It is the most common because it is the **simplest**: there are no
request or response templates to write, no mappings to maintain,
and the Lambda function has full access to the request shape. The
trade-off is that the Lambda function is responsible for building
the response (status code, headers, body), but that is also where
you want the logic to live.

</details>

---

### Q7

What is the difference between a *deployment* and a *stage* in API
Gateway?

<details>
<summary>Show answer</summary>

- A **deployment** is an immutable snapshot of the API's resource
  tree, methods, and integrations at a point in time. You create
  a deployment by clicking "Deploy API" in the console.
- A **stage** is a named, callable reference to a deployment.
  Each stage gets its own URL of the form
  `https://{api-id}.execute-api.{region}.amazonaws.com/{stageName}/`.
  A single API definition can have many stages (`dev`, `staging`,
  `prod`), each pointing at a different deployment.

Stages are the API Gateway equivalent of Lambda aliases (section
11) or git branches / environment promotions: a way to keep
multiple versions of an API live simultaneously under different
URLs.

</details>

---

### Q8

What is a *canary* deployment in API Gateway, and what is it
useful for?

<details>
<summary>Show answer</summary>

A canary is a second deployment attached to the same stage. API
Gateway splits traffic between the "steady" deployment and the
canary according to a percentage you set (e.g. 95% steady, 5%
canary). You watch the canary's CloudWatch metrics for a few
minutes, then promote it to 100% (roll forward) or roll it back.

It is useful for **safe rollouts of a new API version or backend
behavior**. By exposing only a small slice of traffic to the new
version, you limit the blast radius if the new version has a bug.

</details>

---

### Q9

You want to expose a public CRUD API to external customers. Each
customer should be identified and rate-limited, but they are not
AWS users and you do not want them to need AWS credentials. Which
mechanism should you use?

<details>
<summary>Show answer</summary>

**API Key** combined with a **Usage Plan**.

- Issue an API key per customer.
- Attach the key to a usage plan that defines the customer's
  throttle rate, burst, and monthly quota (e.g. "Free tier" with
  10 req/s and 100k req/month, "Pro tier" with 1000 req/s and
  10M req/month).
- Customers pass the key in the `x-api-key` header.

This identifies the customer for metering, enforces rate limits,
and does not require them to have AWS credentials. The customer
keeps the key secret out-of-band; you rotate it by issuing a new
key and deactivating the old one.

</details>

---

### Q10

What is a *private integration* in API Gateway, and what load
balancer type does it require?

<details>
<summary>Show answer</summary>

A **private integration** lets a method's backend live entirely
inside your VPC, with no public IP and no internet traversal. The
backend is fronted by a **Network Load Balancer (NLB)**, and API
Gateway forwards the request to the NLB's listener.

The NLB is required because that is the abstraction API Gateway
knows how to call. You cannot point a private integration directly
at an EC2 instance IP, an ECS service, or an EKS pod — they must
be in an NLB target group.

If your backend is a Lambda function, you do **not** need a
private integration: a Lambda function inside a VPC can reach
private subnets, RDS, ElastiCache, etc. directly using the
Lambda proxy integration from L26. The private integration exists
for non-Lambda backends (EC2, ECS, EKS, internal HTTP services
fronted by an NLB).

</details>
