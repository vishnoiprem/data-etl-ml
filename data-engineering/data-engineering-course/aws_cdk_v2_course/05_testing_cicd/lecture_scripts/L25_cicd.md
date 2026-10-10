---
lecture: L25
title: "CI/CD for CDK — cdk diff in PRs, GitHub Actions, OIDC"
duration: "10:00"
section: 5
prereqs: ["L24"]
---

# L25 — CI/CD for CDK

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 5 — Testing, Snapshots, Assertions, CI/CD
> **Duration:** 10:00

## Prereqs

L24 — Fine-grained assertions

## Key terms

- **`cdk diff`** — show the CloudFormation diff between local code
  and the deployed stack.
- **OIDC** — OpenID Connect. Lets GitHub Actions assume an AWS IAM
  role **without storing long-lived credentials**.
- **GitHub Actions** — the CI runner we'll wire up. Equivalent
  pipelines exist for GitLab, CircleCI, Buildkite, etc.

## Lecture

The canonical CDK CI/CD pipeline has three stages:

```text
PR opened   →   cdk diff  +  npm test    (no deploy)
PR merged   →   cdk deploy (dev)
manual      →   cdk deploy (prod)
```

A minimal GitHub Actions workflow:

```yaml
# .github/workflows/cdk.yml
name: CDK
on:
  pull_request:
  push:
    branches: [main]
jobs:
  cdk:
    runs-on: ubuntu-latest
    permissions:
      id-token: write       # OIDC
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test         # assertions + snapshots
      - run: npx cdk synth --quiet
      - run: npx cdk diff     # only on PRs
      - run: npx cdk deploy --all --require-approval never   # only on main
```

The **OIDC role** is configured once:

```ts
import * as iam from 'aws-cdk-lib/aws-iam';

new iam.Role(this, 'GitHubActionsRole', {
  assumedBy: new iam.WebIdentityPrincipal(
    'token.actions.githubusercontent.com',
    {
      conditions: {
        StringLike: {
          'token-actions.githubusercontent.com:sub': 'repo:myorg/myrepo:*',
        },
      },
    },
  ),
  managedPolicies: [
    iam.ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess'),
  ],
});
```

In production you'd attach a least-privilege policy that only
allows `cloudformation:*` + `s3:*` (for assets) on the
`CDKToolkit` stack, but `AdministratorAccess` is the easiest
starting point.

## Hands-on

There's no CDK project in `05_testing_cicd/code/` for the workflow
file — this is a concepts lecture. To practice:

```bash
mkdir /tmp/gh-actions-cdk && cd /tmp/gh-actions-cdk
cp 02_app_stack_construct/code/hello-cdk -r .
mkdir -p .github/workflows
# paste the workflow above
git init && git add . && git commit -m "add cdk"
gh repo create --public
```

## Quiz prep

- Why use OIDC instead of an access key? (no long-lived secret;
  federated trust scoped to the repo)
- Which command shows the diff between local code and the deployed
  stack? (`cdk diff`)
- When do you run `cdk deploy`? (after merge to main, ideally via
  manual approval for prod)

## Further reading

- [GitHub OIDC for AWS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- Next up: **Section 6 — Real-world patterns (L26+)**
