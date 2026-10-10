# L65 — AWS CloudFormation — REST API and API Resources

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 13
> **Duration target:** 7:17
> **Lecture ID:** L65

## Prereqs

- L62–L64 (S3, IAM, Lambda).
- Section 7 (API Gateway overview) — at minimum L25 and L26.

## Key terms

- **`AWS::ApiGateway::RestApi`** — the container. One per API.
- **`AWS::ApiGateway::Resource`** — a single node in the URL path
  tree. Each resource has a `PathPart` and a `ParentId`.
- **`RootResourceId`** — a special attribute on the `RestApi` that
  points at the implicit `/` resource. Every other resource
  references it (directly or transitively) as its parent.
- **`{proxy+}`** — the "greedy proxy" path parameter. Matches
  anything, including slashes, so `/objects/a/b/c` is captured as
  `proxy = a/b/c`.
- **`EndpointConfiguration`** — `REGIONAL`, `EDGE`, or `PRIVATE`.
  We use `REGIONAL` because we are not putting CloudFront in front
  of the API.

## Lecture

L65 declares the API Gateway container and the two URL resources
the API will expose. We do not add methods yet — that is L66.

### The REST API container

```yaml
ServerlessApi:
  Type: AWS::ApiGateway::RestApi
  Properties:
    Name: l65-serverless-api
    Description: Serverless CRUD API on top of Lambda + S3.
    EndpointConfiguration:
      Types:
        - REGIONAL
```

`AWS::ApiGateway::RestApi` is the *top* resource. Every other
API Gateway resource (resources, methods, deployment, stage) is
attached to this one by `RestApiId: !Ref ServerlessApi`.

`EndpointConfiguration: REGIONAL` means "give me a regional API
endpoint, not a CloudFront-fronted edge endpoint." For our
serverless CRUD app this is the right choice — lower latency, no
edge caching, simpler IAM.

### The resource tree

API Gateway models the URL space as a tree. The root is the
implicit `/` (returned as `RootResourceId` from the `RestApi`
resource). Every other node references a parent:

```text
/
└── /objects                (ParentId = RootResourceId)
    └── /objects/{proxy+}   (ParentId = /objects)
```

We declare two resources:

```yaml
ObjectsResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref ServerlessApi
    ParentId: !GetAtt ServerlessApi.RootResourceId
    PathPart: objects

ObjectKeyResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref ServerlessApi
    ParentId: !Ref ObjectsResource
    PathPart: "{proxy+}"
```

#### Why `{proxy+}` (with the `+`)

The greedy proxy path parameter matches any character, *including
slashes*. So a request to `/objects/2024/01/sales.csv` will
populate `event.pathParameters.proxy = "2024/01/sales.csv"`. The
`+` is what gives you the "catch-all" behavior. The non-greedy
form `{proxy}` matches a single segment only.

If you need a path like `/objects/{key}` with key being a single
segment (no slashes), you can use `{key}` instead. For this use
case we use `{proxy+}` so users can put objects in "folders."

#### `RootResourceId` quirk

`!GetAtt ServerlessApi.RootResourceId` is the only place in the
template where we have to use `!GetAtt` for what is essentially a
"reference to the API itself." API Gateway creates the `/`
resource automatically; you cannot declare it, you can only
reference it.

### Outputs

```yaml
Outputs:
  RestApiId:
    Value: !Ref ServerlessApi
  RootResourceId:
    Value: !GetAtt ServerlessApi.RootResourceId
  ObjectsResourceId:
    Value: !Ref ObjectsResource
  ObjectKeyResourceId:
    Value: !Ref ObjectKeyResource
```

The two resource IDs are going to be picked up by L66 (the
method/deployment) and the L65 standalone template, so it is
worth exposing them as outputs even though we will inline them
with `!Ref` in the full-stack template.

### What you can do with the deployed API at this point

Nothing useful yet. The resources exist in API Gateway but no
method is attached to them, so API Gateway will return
`{"message": "Missing Authentication Token"}` for every URL.

The "deploy" command does succeed though — the resources are
created in API Gateway. In L66 we will add the `Method` blocks
plus a `Deployment` + `Stage`, at which point the API becomes
invokable.

### A note on the `Api` import

If you have ever used `aws apigateway import-rest-api` (the CLI
that takes an OpenAPI spec), you may wonder why we are
hand-writing the resource tree. The reason is pedagogical — when
you hand-declare resources and methods you learn which CFN
properties map to which console setting, which makes the
OpenAPI-based route easier to learn later. Both routes end up at
the same `AWS::ApiGateway::RestApi` resource under the hood.

## Hands-on

1. `aws cloudformation validate-template --template-body file://templates/04_rest_api_resources.yaml`
2. `aws cloudformation deploy --stack-name l65-sandbox --template-file templates/04_rest_api_resources.yaml`
3. Open the API Gateway console, find `l65-serverless-api`, click
   "Resources" — you should see the empty tree (`/`, `/objects`,
   `/objects/{proxy+}`) with no methods.
4. `curl https://<rest-api-id>.execute-api.us-east-1.amazonaws.com/objects/foo` —
   expect `{"message": "Missing Authentication Token"}`.
5. `aws cloudformation delete-stack --stack-name l65-sandbox`

## Quiz prep

- The shape of an API Gateway resource tree.
- The difference between `{proxy}` and `{proxy+}`.
- The two ways to reference the root resource
  (`!GetAtt RestApi.RootResourceId` and `!Ref RestApi`).
- Why the `EndpointConfiguration` choice matters for latency and
  IAM.

## Further reading

- [`AWS::ApiGateway::RestApi` reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-restapi.html)
- [`AWS::ApiGateway::Resource` reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigateway-resource.html)
- [API Gateway path parameters](https://docs.aws.amazon.com/apigateway/latest/developerguide/request-response-path-parameters.html)
