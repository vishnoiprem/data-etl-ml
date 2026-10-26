# Section 4 Quiz — AppSync + Step Functions + EventBridge

> 8 questions, multi-choice. Answers hidden in collapsible blocks.

---

**Q1.** Which CDK construct creates an AppSync GraphQL API?

- A. `apigateway.GraphqlApi`
- B. `appsync.GraphqlApi`
- C. `cloudfront.GraphqlApi`
- D. `aws-cdk-lib/aws-graphql`

<details><summary>Show answer</summary>

**B — `appsync.GraphqlApi`.** It lives under `aws-cdk-lib/aws-appsync`.

</details>

---

**Q2.** Which two ways can you declare a schema in `appsync.GraphqlApi`?

- A. `Schema.fromString` and `SchemaFile.fromAsset`
- B. `Schema.fromYaml` and `Schema.fromJson`
- C. `Schema.open` and `Schema.load`
- D. There's only one — inline string

<details><summary>Show answer</summary>

**A — `Schema.fromString` and `SchemaFile.fromAsset`.** `fromString` is for inline demos; `fromAsset` loads a `schema.graphql` file (the production default).

</details>

---

**Q3.** Which AppSync authorization type is the simplest for public clients?

- A. `API_KEY`
- B. `AWS_IAM`
- C. `AMAZON_COGNITO_USER_POOLS`
- D. `OPENID_CONNECT`

<details><summary>Show answer</summary>

**A — `API_KEY`.** The other three are for internal AWS, Cognito end users, and federated SSO respectively.

</details>

---

**Q4.** What is a "Resolver" in AppSync?

- A. The Lambda function that runs on every API call
- B. The per-field mapping that turns a GraphQL request into a data source call
- C. A DNS resolver for the API's custom domain
- D. The role AppSync uses to call AWS APIs

<details><summary>Show answer</summary>

**B — The per-field mapping.** Without a resolver on a field, AppSync returns `null` for it.

</details>

---

**Q5.** Which data source type does **not** require VTL mapping templates?

- A. DynamoDB
- B. OpenSearch
- C. Lambda
- D. None — all data sources need VTL

<details><summary>Show answer</summary>

**C — Lambda.** Lambda data sources carry the entire context to your function, which returns JSON. Non-Lambda data sources (DynamoDB, OpenSearch, HTTP) execute VTL inside AppSync itself.

</details>

---

**Q6.** Which Step Functions state is a no-op?

- A. `Task`
- B. `Pass`
- C. `Choice`
- D. `Fail`

<details><summary>Show answer</summary>

**B — `Pass`.** Useful for labeling or transforming JSON. It does no work and transitions immediately.

</details>

---

**Q7.** What's the max duration of an Express vs a Standard state machine?

- A. 5 min vs 5 hours
- B. 5 min vs 1 year
- C. 15 min vs 1 day
- D. 1 hour vs 1 year

<details><summary>Show answer</summary>

**B — 5 min (Express) vs 1 year (Standard).** Express is at-least-once with per-execution pricing; Standard is exactly-once with per-transition pricing.

</details>

---

**Q8.** Which CDK construct schedules a Lambda every 5 minutes?

- A. `events.Schedule.rate(...)` on a `Rule`
- B. `lambda.Function.addEventSource(...)`
- C. `apigw.RestApi.schedule(...)`
- D. `cdk.Cron(...)`

<details><summary>Show answer</summary>

**A — `events.Rule` with `Schedule.rate(cdk.Duration.minutes(5))`.** EventBridge is the scheduler; targets are passed via `addTarget(new targets.LambdaFunction(fn))`.

</details>
