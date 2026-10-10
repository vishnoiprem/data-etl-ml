# Section 7 — API Gateway Overview

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 7
> **Lectures:** L25–L29
> **Total duration:** ~30 min
> **Status:** full content in `lecture_scripts/`

## What this section covers

Amazon API Gateway is the "front door" of every serverless application in this
course. Before we build Use Case 2 (a serverless CRUD API on top of S3 with
query string parameters, API keys, and a usage plan) in section 8, you need a
firm grasp of:

- What API Gateway actually is and the three API types it offers
  (REST, HTTP, WebSocket).
- The three endpoint types (edge-optimized, regional, private) and when to
  pick each.
- How an API is structured as a **resource tree** of URIs and HTTP methods,
  and the **integration** layer that maps each method to a backend.
- How **deployments** and **stages** work, what a **canary** is, and how
  **API keys** + **usage plans** throttle and quota your tenants.
- The five supported **authentication and authorization** mechanisms
  (IAM, Cognito User Pool, Cognito Identity Pool, Lambda Authorizer, API Key)
  and when to use which.
- The **private API** model: a REST API that is only reachable from inside
  your VPC, with a **private integration** through a Network Load Balancer
  to an internal service.

## Lecture-to-file map

| L# | Title | Min | File |
|---|---|---|---|
| L25 | API Gateway — Overview, API Types, API Endpoint Types | 7:08 | `lecture_scripts/L25_apigw_overview.md` |
| L26 | API Gateway — Resources, Methods and Integration Types | 5:45 | `lecture_scripts/L26_resources_methods_integrations.md` |
| L27 | API Gateway — Deployment, API Stages, API Keys and Usage Plans | 3:24 | `lecture_scripts/L27_deployment_stages_keys.md` |
| L28 | API Gateway — Authentication and Authorization Methods | 6:48 | `lecture_scripts/L28_auth_methods.md` |
| L29 | API Gateway — Private APIs and Private Integration | 7:04 | `lecture_scripts/L29_private_apis.md` |

## Where this section fits

Section 6 ended with Use Case 1: an S3 → Lambda → DynamoDB pipeline triggered
by an S3 event notification. That use case was a **push** model — the
pipeline reacts to events. Section 7 starts the **pull** model: a client
makes an HTTP call, API Gateway receives it, API Gateway invokes a Lambda
function, and the function returns a response.

The architecture we lay out conceptually in this section is the same one we
will build hands-on in L30–L34 and later in CDK (L71–L77) and
CloudFormation (L60–L70). So when L25 introduces the three API types, think
"which one will Use Case 2 use?" — and keep that answer in your head, because
L30 will confirm it.

## Working artifacts

| # | Artifact | Where | Lectures |
|---|---|---|---|
| 1 | Section-level decision tree (REST vs HTTP vs WebSocket) | `assets/apigw_decision_tree.mmd` | L25 |
| 2 | Resource tree example for Use Case 2 | `assets/usecase2_resource_tree.mmd` | L26 |
| 3 | Quiz | `quizzes/section_7.md` | L25–L29 |

## Prerequisites

- Sections 1–6 completed (you are comfortable with Lambda execution roles,
  CloudWatch logs, and the basic S3/DynamoDB event model).
- An AWS account with permissions to create an API Gateway REST API, Lambda
  function, and IAM role. (We do not create anything in this section — it is
  conceptual — but you will need it from L30 onward.)
- Familiarity with HTTP basics: methods (GET, POST, PUT, DELETE), status
  codes (200, 400, 401, 500), and headers.
