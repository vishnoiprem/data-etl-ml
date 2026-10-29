---
id: L82
title: Section Overview
section: 15
duration: "0:30"
prereqs:
  - L01-L81
---

# L82 — Section Overview — FCI Cluster Monitor

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 15
> **Duration:** 0:30
> **Prereqs:** L01–L81

Welcome to section 15. This is the **third enterprise use case** in the
course. Where section 6 was a fully event-driven file pipeline and
section 8 was a serverless CRUD API, this section tackles an
**operations problem**: a Windows file system in the cloud needs to be
monitored, and when its free storage gets low, the file system has to
grow *itself* and page *ops* with a notification. All of that without
any servers running.

In the next 51 minutes we will cover the architecture in L83, the
two new AWS services — AWS Managed Microsoft AD in L84 and FSx for
Windows File Server in L85 — the Lambda handler in L86, and finally
the wiring of SNS, CloudWatch, and EventBridge in L87. By the end of
L87 you will have a deployable, self-healing, production-shaped
storage monitor that you can hand to a platform team.

## What you will learn

By the end of this section you will be able to:

1. describe the role of AWS Managed Microsoft AD in an FSx for Windows
   deployment and the trade-offs of joining a file system to it;
2. pick the right FSx for Windows storage capacity and throughput
   tier for a given workload and explain how `StorageCapacity` and
   `FreeStorageCapacity` CloudWatch metrics work;
3. write an idempotent Lambda handler that reads a CloudWatch metric
   (or a control-plane value) and grows an FSx volume in a
   controlled, log-audited way;
4. wire an EventBridge scheduled rule, a CloudWatch alarm on
   `AWS/FSx FreeStorageCapacity`, and an SNS topic with an email
   subscription into a single self-healing system;
5. express the whole stack in a single CloudFormation template and
   deploy it with `aws cloudformation package` + `aws cloudformation
   deploy`.

## Key terms

- **FCI** — *File Server Cluster Instance*, the multi-node Windows
  file-server cluster pattern this use case targets.
- **AWS Managed Microsoft AD** — AWS's fully managed, Windows
  Active Directory service. The directory FSx for Windows joins to
  so the file system's users and groups are real AD identities.
- **Amazon FSx for Windows File Server** — fully managed Windows
  file server with SMB, NTFS, and AD integration.
- **EventBridge schedule** — a serverless cron that fires a Lambda
  function on a fixed cadence (every 5 minutes in this course).
- **CloudWatch alarm** — a threshold-based watcher on a CloudWatch
  metric (here: `AWS/FSx FreeStorageCapacity`) that triggers an
  action (here: SNS).
- **Idempotent grow** — calling `fsx.update_file_system` multiple
  times in quick succession has the same effect as calling it once,
  thanks to an in-process cooldown.

## Section map

| L# | Title | Min | File |
|---|---|---|---|
| L82 | Section Overview | 0:30 | `L82_section_overview.md` |
| L83 | Architecture — FCI Cluster Storage Monitor | 6:00 | `L83_architecture.md` |
| L84 | AWS Managed Microsoft AD 101 | 8:00 | `L84_aws_ms_ad.md` |
| L85 | Amazon FSx for Windows File Server 101 | 10:00 | `L85_fsx.md` |
| L86 | The Monitor Lambda — check storage + grow volume | 15:00 | `L86_monitor_lambda.md` |
| L87 | SNS notification + CloudWatch alarm + EventBridge schedule | 12:00 | `L87_sns_cw_eventbridge.md` |

## Quiz prep

You should now be able to answer:

- What problem does the FCI Cluster Monitor solve, and which AWS
  services form the solution?
- Why is the third use case a "monitor + grow" pattern rather than
  a "publish + consume" pattern like sections 6 and 8?
- What does "idempotent grow" mean in this context?

## Further reading

- AWS docs: [What is AWS Managed Microsoft AD?](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_microsoft_ad.html)
- AWS docs: [Amazon FSx for Windows File Server](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/what-is.html)
- AWS docs: [EventBridge scheduled rules](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)
- AWS docs: [Using Amazon CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- L83 — the architecture diagram and the four-question walkthrough
