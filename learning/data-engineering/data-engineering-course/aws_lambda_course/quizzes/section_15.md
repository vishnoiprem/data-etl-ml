# Section 15 Quiz — Enterprise Use Case 3: FCI Cluster Monitor (AWS MS AD, FSx, Lambda, SNS, CloudWatch, EventBridge)

> **Source:** lectures L82–L87
> **Pass bar:** 7 / 10
> Answers are hidden in collapsible blocks. Try the questions first, then
> reveal only one at a time.

**1. What problem does the FCI Cluster Monitor use case solve?**

- A) It scales a SQL Server Failover Cluster Instance by adding
  read-replicas on demand.
- B) It monitors the free storage on an FSx for Windows File Server
  file system joined to AWS Managed Microsoft AD and auto-grows the
  volume when free space runs low.
- C) It backs up an FSx file system to S3 every 24 hours.
- D) It rotates the service account password for AWS Managed
  Microsoft AD on a schedule.

<details><summary>Show answer</summary>

**B)** The FCI Cluster Monitor is an *operations automation* use
case: the file system is joined to an AWS Managed Microsoft AD
directory, and a scheduled Lambda watches the
`FreeStorageCapacity` CloudWatch metric and grows the file system
when it crosses a threshold. SNS notifies ops so a human can review
the auto-grow decisions. The other answers are not what section 15
does.

</details>

---

**2. Which CloudWatch metric does the FCI Cluster Monitor watch?**

- A) `CPUUtilization` on the Lambda function.
- B) `FreeStorageCapacity` on the FSx file system.
- C) `NetworkIn` on the directory controller.
- D) `ApproximateNumberOfMessagesVisible` on the SNS topic.

<details><summary>Show answer</summary>

**B)** The whole section is built around the
`FreeStorageCapacity` CloudWatch metric that FSx for Windows File
Server emits once per minute. The Lambda reads this metric via
`fsx:DescribeFileSystems` (which returns the latest datapoint in the
response) and decides whether to call `fsx:UpdateFileSystem` to
grow the volume. The other options are not the trigger.

</details>

---

**3. What schedules the monitor Lambda?**

- A) An EC2 cron job running every 5 minutes.
- B) A CloudWatch Logs subscription to the FSx log group.
- C) An EventBridge rule with a cron expression.
- D) The AWS Managed Microsoft AD directory's change-notification
  stream.

<details><summary>Show answer</summary>

**C)** The monitor Lambda is invoked by an **EventBridge rule**
with a cron expression (e.g. `cron(*/5 * * * ? *)` for every 5
minutes). There is no EC2 instance, no cron, no daemon — the
schedule is serverless and AWS-managed. The rule's target is the
Lambda ARN; the input is a constant JSON document that the handler
treats as its event.

</details>

---

**4. Why is the FSx file system joined to AWS Managed Microsoft AD?**

- A) Microsoft AD is a free service; joining to it costs nothing.
- B) FSx for Windows File Server requires a Microsoft AD to enforce
  NTFS-style identity, share permissions, and SMB authentication.
- C) The Lambda function uses AD credentials to call the FSx API.
- D) AWS Managed Microsoft AD provides free CloudWatch metrics.

<details><summary>Show answer</summary>

**B)** FSx for Windows File Server is a Windows-native file system
that uses SMB for client access. To get real NTFS-style
authentication, share-level permissions, and Active Directory
group policy, the file system must be joined to a Microsoft AD —
either AWS Managed Microsoft AD, AD Connector, or a self-managed
AD that you reach over a VPN. Without an AD join, the file system
falls back to a local Windows-style account model that does not
integrate with the rest of the customer's identity.

</details>

---

**5. What is the purpose of the `DryRun` parameter on the
CloudFormation stack?**

- A) To skip the IAM role creation.
- B) To run the monitor logic but skip the actual `UpdateFileSystem`
  call, so you can exercise the handler in a test account without
  touching the file system.
- C) To disable CloudWatch metrics.
- D) To prevent the SNS topic from being created.

<details><summary>Show answer</summary>

**B)** `DryRun=true` sets `DRY_RUN=1` in the Lambda's environment.
When the handler sees that flag, it logs the would-be
`UpdateFileSystem` call but does not invoke it. The SNS publish and
the CloudWatch log line still happen, so you can assert on the
side-effects that are safe to exercise in CI. Flip it to `false`
in a real account to allow the actual grow.

</details>

---

**6. What is the cron expression for "every 5 minutes"?**

- A) `cron(0/5 * * * ? *)`
- B) `cron(*/5 * * * *)`
- C) `cron(*/5 * * * ? *)`
- D) `rate(5 minutes)`

<details><summary>Show answer</summary>

**C)** EventBridge cron expressions have **6** fields
(minute, hour, day-of-month, month, day-of-week, year). The
day-of-week and day-of-month fields cannot both be `*` — one of
them must be `?`. So "every 5 minutes" is
`cron(*/5 * * * ? *)`. (A) and (B) are syntactically invalid in
EventBridge; (D) is the rate expression, which is also valid but
*not* a cron expression.

</details>

---

**7. Which AWS service fans out the auto-grow notification to ops?**

- A) CloudWatch Alarms.
- B) EventBridge.
- C) SNS.
- D) SQS.

<details><summary>Show answer</summary>

**C)** The monitor Lambda publishes a single message to an **SNS
topic**. SNS fans out to N subscribers (email, SMS, Lambda, SQS,
HTTPS, mobile push). The CloudFormation stack creates the topic
and the email subscription; you confirm the subscription from your
inbox once. CloudWatch Alarms are a different fan-out primitive
(used for the `FreeStorageCapacity` alarm), and EventBridge is for
event *routing* (not human notification).

</details>

---

**8. Which IAM permissions are *least-privilege* for the monitor
Lambda?**

- A) `AmazonFSxFullAccess` + `AmazonSNSFullAccess` + `*:*`
- B) `fsx:DescribeFileSystems`, `fsx:UpdateFileSystem` on the
  specific file system ARN, `sns:Publish` on the topic ARN, plus
  the standard `logs:CreateLogGroup` / `logs:CreateLogStream` /
  `logs:PutLogEvents`.
- C) `ec2:DescribeInstances`, `s3:GetObject`, `cloudwatch:GetMetricData`.
- D) `iam:PassRole`, `lambda:UpdateFunctionCode`, `sqs:SendMessage`.

<details><summary>Show answer</summary>

**B)** Least privilege is "exactly the calls you need, scoped to
the resource ARNs you need them on." The monitor needs
`fsx:DescribeFileSystems` (to read the current state),
`fsx:UpdateFileSystem` (to grow the volume — scoped to the
specific file system ARN), and `sns:Publish` (scoped to the
specific topic ARN). Plus the standard CloudWatch Logs
permissions. Option (A) is the *managed policy* shortcut that
grants far more than is needed; the section's
`code/monitor_lambda/iam_policy.json` is the explicit
least-privilege version.

</details>

---

**9. How does the test suite verify the monitor's behaviour?**

- A) It calls `fsx:UpdateFileSystem` against a real FSx endpoint.
- B) It uses `moto.mock_aws` to mock FSx + SNS + CloudWatch Logs,
  drives the handler with `code/event_payloads/scheduled_event.json`,
  and asserts on the log lines + the SNS publish.
- C) It relies on a snapshot test of the Lambda's response.
- D) It runs the CloudFormation stack and checks the AWS console.

<details><summary>Show answer</summary>

**B)** The test file
`code/monitor_lambda/test_lambda_function.py` uses
`@mock_aws` from `moto >= 5.0` to mock the boto3 clients. The
fixture is the same JSON payload that EventBridge will deliver
in production. The test asserts the handler returns 0, the SNS
publish happened, and the CloudWatch log group received the
expected `would-grow` line. This is the same pattern you have
seen in sections 6 and 8: moto + a JSON fixture = an end-to-end
test with zero AWS spend.

</details>

---

**10. Which of these is the right tool when the workload is Linux
EBS volumes (not FSx for Windows)?**

- A) Section 15's pattern, with `ec2:DescribeVolumes` instead of
  `fsx:DescribeFileSystems` and `ec2:ModifyVolume` instead of
  `fsx:UpdateFileSystem`.
- B) The same exact code; the AWS APIs are interchangeable.
- C) Section 8's Use Case 2 stack.
- D) A new, separate use case that has no relation to section 15.

<details><summary>Show answer</summary>

**A)** Section 15's *shape* — scheduled Lambda + CloudWatch
metric + auto-grow + SNS — is the right tool. You only have to
swap the FSx API calls for the equivalent EBS API calls:
`ec2:DescribeVolumes` returns the same `FreeStorageCapacity`
shape, and `ec2:ModifyVolume` is the EBS analogue of
`fsx:UpdateFileSystem`. The CloudWatch alarm name, the
EventBridge rule, and the SNS topic are identical. The
section's `assignments/assignment_7_fci_monitor.md` asks
you to do exactly this swap as an extension.

</details>
