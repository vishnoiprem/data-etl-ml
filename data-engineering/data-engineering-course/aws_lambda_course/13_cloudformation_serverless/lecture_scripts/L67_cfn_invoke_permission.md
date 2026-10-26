# L67 — AWS CloudFormation — Lambda Invoke Permission

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 13
> **Duration target:** 4:29
> **Lecture ID:** L67

## Prereqs

- L66 (Method and Deployment) — you saw `AccessDenied` from your
  curl because the permission was not there yet.

## Key terms

- **`AWS::Lambda::Permission`** — a resource policy attached to a
  Lambda. It grants another principal permission to call
  `lambda:InvokeFunction` on the function.
- **Resource-based policy** — IAM policies attached to a specific
  resource (Lambda, SNS topic, S3 bucket, SQS queue) rather than
  to an IAM identity. They are the only way to grant
  cross-account access to Lambda without an IAM role.
- **`SourceArn`** — the ARN pattern that the calling service is
  allowed to invoke from. We use the
  `arn:aws:execute-api:<region>:<account>:<api-id>/*/<method>/<path>`
  pattern so only API Gateway can invoke the function.

## Lecture

After L66 the API is "deployable" but if you hit it with `curl`
you will see:

```
{"message": "User: arn:aws:sts::...:assumed-role/... is not authorized
 to perform: lambda:InvokeFunction on resource:
 arn:aws:lambda:...:function:l64-get-object"}
```

This is the **Lambda-side** of the cross-service authorization
graph. API Gateway will only call a Lambda if the Lambda has a
resource-based policy (an `AWS::Lambda::Permission`) that says
"the `apigateway.amazonaws.com` principal is allowed to call
`lambda:InvokeFunction` on me."

API Gateway does not assume a role when it invokes a Lambda —
the invocation flows over the Lambda service's
account-to-account control plane, and Lambda checks the
resource policy on the way in.

### The permission

```yaml
GetInvokePermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref GetObjectFunctionArn
    Action: lambda:InvokeFunction
    Principal: apigateway.amazonaws.com
    SourceArn: !Sub "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${ServerlessApi}/*/GET/objects/*"
```

Four properties.

#### `FunctionName`

The Lambda to authorize. `!Ref` on a function returns the ARN;
the `AWS::Lambda::Permission` resource accepts either the name
or the ARN, but the ARN is more robust if there is ever
ambiguity.

#### `Action`

Always `lambda:InvokeFunction`. There is one action for
invocations.

#### `Principal`

Always `apigateway.amazonaws.com` for this integration. Note this
is a **service** principal, not an AWS account principal, so it
is a static string rather than an `AWS:` block.

#### `SourceArn`

The pattern that locks the permission down to *one specific
API + one method + one path*. Concretely:

```
arn:aws:execute-api:<region>:<account>:<api-id>/<stage-or-*>/
    <http-method>/<resource-path>
```

For `GET /objects/{proxy+}` we use
`<api-id>/*/GET/objects/*` — the `*` in the stage position
catches every stage (so the permission works in `prod`, `staging`,
etc.), and the trailing `*` matches the `{proxy+}` greedy path
parameter.

If you omit `SourceArn` entirely, the function is **publicly
invocable by any AWS caller** from any API Gateway, which is
rarely what you want.

### One permission per method

We declare two permissions — one for GET, one for PUT. The
template is repetitive but each method has its own ARN pattern
(`/*/GET/...` vs `/*/PUT/...`), so we cannot collapse them into a
single resource.

### Why not on the IAM role instead?

You might ask: "Why not just add `lambda:InvokeFunction` to the
Lambda execution role?" That would not work, because:

- The role is assumed by the *Lambda execution environment*, not
  by *API Gateway*.
- When API Gateway invokes the function it does not assume any
  role — it makes a direct service-to-service call. The relevant
  IAM check is on the function's **resource policy**, not on a
  role.

Resource-based policies are the bridge for service-to-service
calls in this corner of AWS.

### Validation gotcha

If you forget the permission, you do not get a CFN error — the
template deploys cleanly and the failure surfaces only when the
client calls the API. So always smoke-test after deploy:

```bash
curl -i "$(aws cloudformation describe-stacks \
  --stack-name l66-sandbox \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)/objects/hello.txt"
```

A 502 with `Internal server error` and an API Gateway log
"Execution failed due to configuration error: Invalid
permissions on Lambda function" means the permission is
missing.

## Hands-on

1. Add the `AWS::Lambda::Permission` blocks (already included in
   `templates/05_method_deployment.yaml` — open the file and read
   them).
2. Re-deploy L66 with `aws cloudformation deploy ... --capabilities CAPABILITY_IAM`.
3. Hit the API: expect a 200 (or 404 if the object does not
   exist — that is the Lambda's `NoSuchKey` response, which is
   fine).
4. To verify the permission independently:
   `aws lambda get-policy --function-name l64-get-object` shows
   the resource policy.
5. `aws cloudformation delete-stack --stack-name l66-sandbox`

## Quiz prep

- The four properties of `AWS::Lambda::Permission`.
- Why a Lambda execution role is *not* sufficient and you need
  the resource policy too.
- The shape of the `SourceArn` for an API Gateway integration.
- Why one permission per method is the right granularity.

## Further reading

- [`AWS::Lambda::Permission` reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-permission.html)
- [Lambda resource-based policies](https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html)
- [API Gateway IAM permissions](https://docs.aws.amazon.com/apigateway/latest/developerguide/permissions.html)
