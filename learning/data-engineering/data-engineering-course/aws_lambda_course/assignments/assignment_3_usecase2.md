# Assignment 3 — Use Case 2 CRUD API with Cognito + WAF + Throttling

> **Section:** 8 (Use Case 2) + 7 (API Gateway) + 9 (Cognito Authorizer)
> **Estimated time:** 8 hours
> **Deliverable:** A working REST API in front of a Lambda + S3 backend, protected by Cognito, throttled, and fronted by a WAF rate-based rule.
> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Learning objectives

By the end of this assignment you will be able to:

1. Stand up an **API Gateway REST API** with `/items` (GET, POST, PUT, DELETE) backed by a single Lambda integrator.
2. Add a **Cognito User Pool Authorizer** to the API and use the returned IAM policy to scope per-method access.
3. Add a **`/health` endpoint** that returns `200 OK` with a JSON body and is **unauthenticated**.
4. Configure **throttling** at both the stage and the usage-plan level, and prove the limit is enforced.
5. Attach a **WAFv2 WebACL** with a rate-based rule (200 requests / 5 min) and observe `429` from CloudWatch metrics.
6. Use SAM or CDK to model the entire stack.

## Background

Section 8 builds a CRUD API over an S3 bucket. The lecture is console-first; this assignment ports the architecture to code and adds the production safeguards that section 9 introduces at the protocol level. The result should be a single `sam deploy` (or `cdk deploy`) that creates everything.

## Architecture

```
Client ──HTTPS──▶ API Gateway ──Cognito auth──▶ Lambda ──▶ S3 (items/)
                  │                │
                  │                └─IAM policy from idToken claim
                  │
                  ├──/health (public, no auth)
                  └──throttle: 100 RPS burst 200, WAF rate-based: 200 / 5 min
```

See `assets/architecture_usecase2.mmd`.

## Step-by-step tasks

### Step 1 — Pick the deploy mechanism (SAM or CDK)

Same choice as assignment 2. **SAM is recommended** for this assignment because the throttling and WAF resources are easier to express in YAML than in CDK construct props.

### Step 2 — Build the CRUD Lambda

`handler/app.py` — single function that dispatches on `event["httpMethod"]`:

| Method | Path | Behavior |
|---|---|---|
| `GET`    | `/items/{id}`  | `s3.get_object` and return the body. `404` if missing. |
| `GET`    | `/items`       | `s3.list_objects_v2` on `items/` and return the keys + sizes. |
| `POST`   | `/items`       | Body is the JSON record; write to `items/{id}.json`. |
| `PUT`    | `/items/{id}`  | Upsert. |
| `DELETE` | `/items/{id}`  | Delete. |
| `GET`    | `/health`      | Return `{"status": "ok", "ts": "<ISO>"}`. |

Hard requirements:

- The handler must work whether `event["httpMethod"]` is uppercase (REST) or lowercase (HTTP API). Normalize.
- All responses must follow the shape `{"statusCode": int, "headers": {...}, "body": str}`. Set `Content-Type: application/json`.
- Errors must be JSON: `{"error": "NotFound", "message": "..."}`. Use a custom exception class and a top-level `try/except` decorator.

### Step 3 — Define the API in SAM

```yaml
Resources:
  ItemsApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Auth:
        DefaultAuthorizer: CognitoAuthorizer
        Authorizers:
          CognitoAuthorizer:
            UserPoolArn: !GetAtt UserPool.Arn
      MethodSettings:
        - ResourcePath: /*
          HttpMethod: '*'
          ThrottlingBurstLimit: 200
          ThrottlingRateLimit: 100
  ItemsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handler/
      Handler: app.handler
      Runtime: python3.12
      MemorySize: 256
      Timeout: 15
      Policies:
        - S3CrudPolicy:
            BucketName: !Ref ItemsBucket
      Events:
        GetItem:
          Type: Api
          Properties:
            RestApiId: !Ref ItemsApi
            Path: /items/{id}
            Method: GET
        ListItems:
          Type: Api
          Properties: {RestApiId: !Ref ItemsApi, Path: /items, Method: GET}
        CreateItem:
          Type: Api
          Properties: {RestApiId: !Ref ItemsApi, Path: /items, Method: POST}
        UpdateItem:
          Type: Api
          Properties: {RestApiId: !Ref ItemsApi, Path: /items/{id}, Method: PUT}
        DeleteItem:
          Type: Api
          Properties: {RestApiId: !Ref ItemsApi, Path: /items/{id}, Method: DELETE}
  HealthFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: health/
      Handler: app.handler
      Runtime: python3.12
      Events:
        Health:
          Type: Api
          Properties:
            RestApiId: !Ref ItemsApi
            Path: /health
            Method: GET
            Auth:
              Authorizer: NONE
  ItemsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub usecase2-items-${AWS::AccountId}
      PublicAccessBlockConfiguration:
        BlockAllPublicAccess: true
  UserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      UserPoolName: usecase2-users
      AutoVerifiedAttributes: [email]
      UsernameAttributes: [email]
      Schema:
        - {Name: email, AttributeDataType: String, Required: true, Mutable: true}
  UserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref UserPool
      ExplicitAuthFlows: [ALLOW_USER_PASSWORD_AUTH, ALLOW_REFRESH_TOKEN_AUTH]
      GenerateSecret: false
Outputs:
  ApiUrl:        {Value: !Sub "https://${ItemsApi}.execute-api.${AWS::Region}.amazonaws.com/prod"}
  UserPoolId:    {Value: !Ref UserPool}
  UserPoolClientId: {Value: !Ref UserPoolClient}
  BucketName:    {Value: !Ref ItemsBucket}
```

### Step 4 — Add the WAF WebACL

```yaml
  ItemsWebAcl:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: usecase2-acl
      Scope: REGIONAL
      DefaultAction: {Allow: {}}
      Rules:
        - Name: RateLimit200per5min
          Priority: 1
          Statement:
            RateBasedStatement:
              Limit: 200
              AggregateKeyType: IP
          Action: {Block: {}}
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: RateLimit
      VisibilityConfig:
        SampledRequestsEnabled: true
        CloudWatchMetricsEnabled: true
        MetricName: ItemsWebAcl
  ItemsWebAclAssociation:
    Type: AWS::WAFv2::WebACLAssociation
    Properties:
      ResourceArn: !Sub "arn:aws:apigateway:${AWS::Region}::/restapis/${ItemsApi}/stages/prod"
      WebACLArn: !GetAtt ItemsWebAcl.Arn
```

### Step 5 — Create a Cognito user and get an id token

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username alice@example.com \
  --user-attributes Name=email,Value=alice@example.com Name=email_verified,Value=true \
  --temporary-password 'TempPass!23' --message-action SUPPRESS
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID --username alice@example.com \
  --password 'Passw0rd!2026' --permanent
ID_TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $USER_POOL_CLIENT_ID \
  --auth-parameters USERNAME=alice@example.com,PASSWORD='Passw0rd!2026' \
  --query 'AuthenticationResult.IdToken' --output text)
```

### Step 6 — Hit the API

```bash
curl -i "$API_URL/health"                           # expect 200
curl -i -H "Authorization: $ID_TOKEN" "$API_URL/items"
curl -i -X POST -H "Authorization: $ID_TOKEN" -H "Content-Type: application/json" \
  -d '{"id":"sku-1","name":"widget","price":9.99}' "$API_URL/items"
curl -i -H "Authorization: $ID_TOKEN" "$API_URL/items/sku-1"
curl -i -X DELETE -H "Authorization: $ID_TOKEN" "$API_URL/items/sku-1"
```

### Step 7 — Prove the WAF rule

Run a tight loop:

```bash
for i in $(seq 1 250); do
  curl -s -o /dev/null -w "%{http_code}\n" "$API_URL/health"
done | sort | uniq -c
```

You should see a mix of `200` and `403` (WAF Block produces a 403 from API Gateway). Confirm in the CloudWatch metric `RateLimit` for the WebACL.

### Step 8 — Document everything in a README

Same structure as assignment 2, plus a **Security** section listing the Cognito + WAF + throttling controls and the exact CLI commands to test each.

## Deliverables

- [ ] Full source tree (SAM `template.yaml` + `handler/` + `health/`, or CDK equivalent).
- [ ] `README.md` (Architecture, Prereqs, Deploy, Invoke, Throttle test, WAF test, Cognito token, Cleanup, Security).
- [ ] Successful `sam deploy` log or `cdk deploy` summary.
- [ ] `curl` transcripts for all six endpoints.
- [ ] WAF proof: 250-request loop output showing the `403`s.
- [ ] CloudWatch screenshot or `aws cloudwatch get-metric-statistics` JSON for the `RateLimit` metric.

## Grading rubric (100 points)

| Category | Points | What we look for |
|---|---|---|
| CRUD correctness | 20 | All five methods (GET, POST, PUT, DELETE, LIST) work against S3. |
| `/health` is public | 5 | Returns 200 without an `Authorization` header. |
| Cognito auth | 20 | All `/items*` endpoints reject unauthenticated requests with 401. |
| Throttling | 15 | Burst and rate limits are set; abusive load gets `429`. |
| WAF | 20 | WebACL attached, rate-based rule fires, CloudWatch metric visible. |
| README | 10 | Has Security section, all commands copy-pasteable. |
| Cleanup | 10 | `sam delete` removes every resource including the WebACL. |

Deductions:

- `-10` if the Cognito authorizer is attached at the **API level** but not actually **enforced** (i.e., methods that should be protected are reachable anonymously).
- `-10` if the WAF is in scope `CLOUDFRONT` instead of `REGIONAL` for an API Gateway REST API.
- `-10` if cleanup leaves any non-empty S3 bucket behind.

## Stretch goals (optional, +10 each, capped at +20)

- Swap the Cognito authorizer for a **Lambda authorizer** (see assignment 4).
- Add a **request validator** so the POST body is checked against a JSON schema.
- Add **X-Ray** tracing and demonstrate the service map in the console.
- Add a **custom domain** with an ACM certificate and a Route 53 alias record.
