---
lecture: L30
title: "Course wrap-up — CDK vs CFN in 2026, when to reach for what"
duration: "12:00"
section: 6
prereqs: ["L29"]
---

# L30 — Course Wrap-Up — CDK vs CFN in 2026

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 6 — Real-World Patterns
> **Duration:** 12:00

## Prereqs

L29 — Aspects

## Key terms

- **Default IaC** — the tool you reach for by default. Most teams
  should pick one and standardize.
- **CDK → CFN pipeline** — the deployment path; everything
  eventually becomes a CloudFormation change set.
- **Code organization at scale** — how to keep a large CDK app
  maintainable.

## Lecture

Six sections, 30 lectures, 3 working TypeScript projects, 6
quizzes. Here's the 2026 default-recommendation cheat sheet:

| Situation | Use |
|---|---|
| Single AWS account, ≤ 50 resources, TS team | **CDK v2** (this course) |
| Single AWS account, large team, must be readable by ops | **CDK v2** with `cdk synth` → committed JSON, then **CFN** for review |
| Single AWS account, no programming background | **CloudFormation YAML** |
| Multi-cloud | **Terraform** (or **Pulumi** if you want a real language) |
| New AWS service, CDK L2 doesn't exist yet | **CDK L1** (escape hatch) |
| Demo / 1-day prototype | **CDK v2** wins on conciseness |

**What you can now do:**

- Build, test, and deploy a multi-stack CDK app from scratch.
- Write a Jest test suite that catches both property-level and
  template-level regressions.
- Wire CI/CD with OIDC and `cdk diff` in PRs.
- Use Aspects to enforce organization-wide compliance.
- Decide when to reach for the escape hatch and drop to L1.

**What's next (optional follow-ups):**

- **Pulumi** for multi-cloud IaC with a real language.
- **CDK Pipelines** (`aws-cdk-lib/pipelines`) for self-mutating
  multi-stage CI/CD.
- **AWS Proton** for "service templates" that wrap CDK apps.
- **Terraform CDK** (`cdktf`) if you really want to be at every
  party.

**Where to go from here:**

- The official [CDK Workshop](https://cdkworkshop.com/) is the
  canonical hands-on follow-up.
- [Awesome CDK](https://github.com/kolomied/awesome-cdk) is a
  curated list of L3 patterns and example projects.
- The `#cdk` channel on the [AWS Developers Slack](https://awsdevelopers.slack.com/).

## Hands-on

```bash
# final smoke test on the course's projects
cd aws_cdk_v2_course
python3 scripts/run_all_tests.py --skip-install   # skip npm install
```

You should see 3 projects listed and a graceful "npm not on PATH"
or "all tests passed" summary.

## Quiz prep

- Which tool is the default recommendation for a single-AWS-account
  TypeScript team? (CDK v2)
- What wraps a CDK app into a self-mutating CI/CD pipeline?
  (CDK Pipelines)

## Further reading

- [`../SYLLABUS.md`](../SYLLABUS.md) — full lecture map
- [`../DIRECTORY.md`](../DIRECTORY.md) — full file index
- [`../CHANGELOG.md`](../CHANGELOG.md) — course changelog

---

**That's the end. Thanks for taking the course — now go build
something.**

— *Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
