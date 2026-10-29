---
id: L29
title: "API Gateway — Private APIs and Private Integration"
section: 7
duration: "7:04"
author: "Prem Vishnoi <pvishnoi@avilx.com>"
udemy_id: 29
---

# L29 — API Gateway — Private APIs and Private Integration

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 7 — API Gateway Overview
> **Lecture duration target:** 7:04

## Prereqs

- L25, L26, L27, L28. You should know what a REST API is, how
  resources/methods/integrations work, and how the five auth
  mechanisms plug in.
- L51–L52 (section 11) — Lambda VPC networking. Specifically, you
  should be comfortable with the idea of a Lambda function executing
  inside a VPC, talking to private subnets, and using an ENI for
  network identity.
- Comfort with VPC concepts: subnets, route tables, security groups,
  and the basic shape of an AWS network.

## Key terms

- **Private API** — a REST API whose URL is only resolvable from
  inside a VPC. There is no public DNS. AWS calls this an
  "AWS PrivateLink" pattern.
- **Interface VPC endpoint** — an ENI in your subnet powered by
  PrivateLink. Resolves a special AWS service DNS name to a private
  IP. You create one of these for `com.amazonaws.{region}.execute-api`
  to reach a private API.
- **Resource policy** — a JSON policy document you attach to a
  private API. It declares *which VPCs and which principals* may
  invoke the API. Acts as a VPC-level firewall for the API.
- **Private integration** — a method whose backend is a resource in
  your VPC, reached through a **Network Load Balancer (NLB)**.
- **Network Load Balancer (NLB)** — Layer-4 (TCP) load balancer in
  your VPC. API Gateway's private integration uses the NLB to
  forward the request to a target group that contains the
  actual backend (EC2 instance, IP, or another ENI).
- **VPC endpoint policy** — a resource policy on the
  `execute-api` VPC endpoint. It can further restrict which APIs the
  VPC endpoint can reach.

## Lecture

Sometimes you build an API that is *not* for the public internet. It
might be a microservice inside your organization, a control plane
that only your own services should hit, or a regulated workload that
must never leave your VPC. For those, you build a **private API**:
a REST API with no public URL, reachable only through a VPC
endpoint. L29 is about how that works and how the *private
integration* variant lets the API itself call back into a private
backend in your VPC.

### The shape of a private API

A private API is created just like any other REST API except you
pick "Private" as the endpoint type. API Gateway generates a
`{api-id}.execute-api.{region}.amazonaws.com` URL, but that URL
will not resolve from the public internet; it resolves only through
the **PrivateLink DNS** that AWS attaches to a VPC endpoint you
create.

The wiring is:

1. In API Gateway, create a REST API with endpoint type
   `Private`.
2. Attach a **resource policy** to the API. The policy declares
   which VPCs (by VPC ID or by `aws:SourceVpc` condition) and which
   principals are allowed to call `execute-api:Invoke`. This is
   your VPC-level allow-list.
3. In the VPC that should reach the API, create an **interface VPC
   endpoint** for the service
   `com.amazonaws.{region}.execute-api`. AWS creates an ENI in a
   subnet you choose and attaches a private hosted zone so
   `*.execute-api.{region}.amazonaws.com` resolves to a private IP.
4. From an EC2 instance, a Lambda function inside a VPC, or any
   other workload in that VPC, call the API's URL. The DNS
   resolves to the VPC endpoint ENI, traffic flows over the AWS
   private network, and the resource policy is evaluated.

There is no internet hop, no public IP, no NAT. The traffic stays
on the AWS backbone the entire way.

### Resource policy

A resource policy on a private API looks very much like an S3
bucket policy. A minimal example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:us-east-1:123456789012:abc123def/*",
      "Condition": {
        "StringEquals": {
          "aws:SourceVpc": "vpc-0123abcd"
        }
      }
    }
  ]
}
```

The `aws:SourceVpc` condition restricts the API to one specific VPC.
You can also use `aws:SourceVpce` to restrict to one specific VPC
endpoint, which is tighter and recommended for production.

### Private integration: API Gateway calling a VPC backend

A private API is most powerful when combined with a **private
integration**. A private integration lets a method call a backend
that lives entirely inside your VPC — typically an EC2 instance, a
container service, or an internal HTTP service fronted by an NLB —
without exposing that backend to the public internet either.

The wiring is:

1. Deploy your backend (say, an EC2 instance running an HTTP server
   on port 8080) in private subnets.
2. Create an **internal** NLB in front of the backend, with a
   target group that contains the EC2 instance.
3. In API Gateway, create a `VPCLink` resource that points at the
   NLB. (A VPCLink is API Gateway's name for the NLB attachment.)
4. Configure the method's integration as "Private integration" with
   the VPCLink, and supply the listener port of the NLB.
5. When the method is invoked, API Gateway makes an HTTP request to
   the NLB, which forwards to the EC2 instance. The instance never
   needs a public IP and the response flows back to the client.

The key constraint: a private integration's backend **must be
fronted by an NLB**. You cannot point it directly at an EC2
instance IP, an ECS service, or an EKS pod. The NLB is the
abstraction API Gateway knows how to call.

### Private integration vs Lambda proxy

You may be thinking: "couldn't I just have a Lambda function
inside a VPC, and use the Lambda proxy integration from L26 to
reach my VPC resources?" The answer is yes, and for most serverless
backends that is the right answer — a Lambda function in a VPC
with the right security group can call private RDS, ElastiCache,
internal HTTP services, etc. without an NLB.

The private integration exists for the case where your backend is
*not* a Lambda function. Examples:

- A long-running service deployed on EC2, ECS, or EKS that you
  want to expose as an API.
- An internal SaaS-style product that already speaks HTTP and
  lives behind an NLB.
- A multi-tenant control plane that mixes Lambda for some
  endpoints and a long-running service for others.

### Why this matters

Private APIs and private integrations are the most common pattern
for **internal** microservice architectures on AWS. The public
internet never sees the API URL or the backend. The resource
policy + VPC endpoint combination gives you defense in depth: even
if someone exfiltrates an API ID, they cannot call the API from
outside the allowed VPCs.

For Use Case 2 (section 8) we will *not* use a private API — that
use case is a public CRUD API. But L29 gives you the conceptual
vocabulary for the kind of architecture you would build if you
were re-platforming an internal microservice onto API Gateway, and
for the GenAI Bedrock use case in section 10 if you wanted to keep
the API inside the corporate network.

## Hands-on

Conceptual. There is no hands-on for L29 in this section. If you
want to peek ahead, the workflow is:

1. Create a REST API with endpoint type "Private."
2. Attach a resource policy that allows your VPC.
3. Create an interface VPC endpoint for
   `com.amazonaws.{region}.execute-api` in the VPC.
4. From an EC2 instance in that VPC, `curl` the API's
   `execute-api` URL. You should see the method's response.
5. From your laptop on the public internet, the same `curl`
   should fail (DNS will not resolve, or the connection will be
   refused).

The CDK v2 walkthrough in L77 and the CloudFormation walkthrough
in L60–L70 cover the IaC for both public and private REST APIs.

## Quiz prep

1. What is a private API, and what AWS feature powers it?
2. What is a resource policy on a private API, and what condition
   key do you use to restrict access to a specific VPC?
3. What is a private integration, and what load balancer type
   does it require?
4. Why can't a private integration point directly at an EC2
   instance's private IP?
5. If your backend is a Lambda function, do you need a private
   integration? Why or why not?

## Further reading

- AWS Docs — *Create a private REST API*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-private-apis.html
- AWS Docs — *Use an interface VPC endpoint for a private REST
  API*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/private-api-set-up.html
- AWS Docs — *Set up private integrations with REST APIs*:
  https://docs.aws.amazon.com/apigateway/latest/developerguide/private-integration.html
- L30 — *Serverless Enterprise Use Case 2 — Architecture*. We
  build the public version of the same pattern in section 8.
