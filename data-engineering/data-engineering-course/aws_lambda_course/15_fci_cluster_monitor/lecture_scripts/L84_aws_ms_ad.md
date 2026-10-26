---
id: L84
title: AWS Managed Microsoft AD 101
section: 15
duration: "8:00"
prereqs:
  - L82-L83
---

# L84 — AWS Managed Microsoft AD 101

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 15
> **Duration:** 8:00
> **Prereqs:** L82–L83

## What you will learn

By the end of this lecture you will be able to:

1. describe what AWS Managed Microsoft AD is, what it is *not*, and
   when to use it;
2. explain the directory structure AWS Managed Microsoft AD
   provisions and how to connect a Windows workload to it;
3. articulate the trust and DNS relationships between an AWS Managed
   Microsoft AD, an FSx for Windows file system, and the rest of
   the VPC;
4. join an FSx for Windows file system to an existing directory and
   verify the join;
5. decide between AWS Managed Microsoft AD, AD Connector, and
   self-managed AD for a given workload.

## Key terms

- **Active Directory (AD)** — Microsoft's directory service for
  Windows networks. Stores users, groups, computers, group policy
  objects, and DNS records.
- **Domain Controller (DC)** — the Windows Server role that
  hosts a copy of the AD database, handles authentication, and
  replicates with peer DCs.
- **AWS Managed Microsoft AD** — a fully managed, AWS-operated AD
  in your VPC. AWS runs two domain controllers in separate AZs
  for you.
- **Directory ID (`d-xxxxxxxxxx`)** — the unique identifier for an
  AWS Managed Microsoft AD. FSx for Windows references it by
  this ID.
- **DNS** — the name-resolution service. AWS Managed Microsoft AD
  provides DNS for the directory's domain (e.g. `corp.example.com`).
- **Trust relationship** — an explicit, bidirectional or
  unidirectional trust between two AD domains that lets users in
  one domain authenticate to resources in the other.
- **AD Connector** — a directory gateway that proxies auth
  requests to on-premises AD. *Not* a directory; it relays.
- **Self-managed AD on EC2** — the legacy approach: run Windows
  Server on EC2, install AD DS, manage the DCs yourself.
- **FSx for Windows File Server** — managed Windows file system;
  integrates with AD for SMB authentication, NTFS ACLs, and
  Kerberos.

## What AWS Managed Microsoft AD is

AWS Managed Microsoft AD is a **fully managed Active Directory**
running on Windows Server inside your VPC. When you create one, AWS:

1. stands up **two Windows Server domain controllers** in different
   Availability Zones in the VPC you choose;
2. promotes them to domain controllers for the **fully qualified
   domain name (FQDN)** you specify (e.g. `corp.example.com`);
3. runs them on managed EC2 instances, patches them, monitors them,
   and takes care of replication;
4. publishes the directory's DNS service on two **ENIs in the
   directory's subnets** so workloads in the VPC can resolve
   `corp.example.com` and reach the DCs;
5. enforces AWS-side security: the DCs are isolated, you cannot
   RDP into them directly, and you cannot manage them as if they
   were EC2 instances.

In short: AWS runs AD for you so you do not have to babysit
Windows Server.

### What it is *not*

- It is not **AWS Directory Service for Simple AD** (the cheaper,
  Samba-based directory). Simple AD is fine for Linux workloads
  that need basic LDAP; it is not real Active Directory and
  cannot host Windows trusts or Group Policy.
- It is not **Amazon Cognito** (the user pool for SaaS apps).
  Cognito is for app-level identity, not for Windows / SMB / NTFS
  identity.
- It is not **AWS Single Sign-On / IAM Identity Center**. SSO is
  for federating *into* the AWS console and SaaS apps; Managed
  Microsoft AD is the directory-of-record for Windows workloads.

## When to use AWS Managed Microsoft AD

Use it when you have any of the following:

- **FSx for Windows File Server** in production and you need real
  NTFS ACLs and SMB Kerberos authentication tied to corporate
  identities. (This is our use case in section 15.)
- **Windows EC2 instances** that need to join a domain for Group
  Policy, software deployment, or scheduled tasks that require
  domain credentials.
- **AWS workloads that must trust an on-premises AD forest** so
  on-prem users can authenticate to cloud resources. AWS Managed
  Microsoft AD supports one-way and two-way external trusts with
  on-premises forests.
- **SQL Server Always On, RDS for SQL Server Multi-AZ**, or other
  Windows-integrated services that need Kerberos.

Do *not* use it when:

- your workload is **pure Linux or containers** — there is no
  benefit and you are paying for Windows licences you do not
  need;
- you have a **single-account, single-region** test environment —
  the per-hour pricing for two managed DCs is overkill;
- you only need a **single sign-on to a SaaS app** — Cognito or
  IAM Identity Center is cheaper and simpler.

## The directory structure AWS provisions

When you create an AWS Managed Microsoft AD with the FQDN
`corp.example.com`, AWS creates:

- a **forest** with one **domain** `corp.example.com`;
- two **domain controllers** (DCs), one per AZ, each named
  `d-xxxxxxxxxx.corp.example.com` under the hood;
- the **Domain Admins**, **Enterprise Admins**, **Schema Admins**,
  **Administrators** groups, with the `Admin` account you chose
  during creation as the first domain admin;
- the **Organizational Unit (OU) `AWS Delegated Groups`** for AWS
  to populate with delegated groups like `AWS Delegated
  Administrators`, `AWS Delegated Security Auditors`, and so on;
- the **default Domain Password Policy** (90-day max age,
  complexity on, etc.);
- the **DNS zones** `corp.example.com` and the in-addr.arpa
  reverse zone for the VPC;
- an **AWS Delegated Security Auditors** group with read-only
  rights across the directory so your security team can audit
  without joining Domain Admins.

You can create additional OUs, GPOs, users, and groups in the
normal ways — through the **Active Directory Users and Computers**
MMC snap-in from a domain-joined Windows EC2 instance, or
programmatically with the `dsadd`, `dsmod`, `New-ADUser` (PowerShell)
or `ldap3` (Python) tools.

## DNS, subnets, and the VPC plumbing

A directory is **scoped to two subnets** in your VPC. AWS puts one
DC in each subnet, and each DC's NIC becomes a **DNS server** for
the directory's domain. Any EC2 instance in the VPC that points
its VPC DNS resolver at the directory's DNS server IPs (or just
uses the VPC's default resolver) can resolve `corp.example.com`
hostnames and reach the DCs.

You must make sure the two subnets:

- are in **different Availability Zones**;
- are in the **same VPC** as the FSx file system (or peered /
  transit-routed);
- have **outbound internet access** (via a NAT gateway or
  transit gateway) so the DCs can phone home for Windows
  activation and patching — Managed Microsoft AD requires this
  and the stack creation will fail without it;
- have the directory's security group applied — Managed Microsoft
  AD creates the SG for you; you do not edit it.

A common gotcha: the **subnet's CIDR must have at least 3 free IP
addresses** at directory-create time, and AWS reserves a /22 of
private IPs inside each subnet for the directory's ENIs. Pick
subnets with `/24` or larger to leave room.

## Joining an FSx file system to the directory

Once the directory is `Active`, you can join an FSx file system
to it. In the FSx console:

1. **Create file system** → **Amazon FSx for Windows File Server**.
2. Pick a VPC and the two subnets for the file system's
   **preferred** and **standby** file servers.
3. Under **Windows authentication**, choose **AWS Managed
   Microsoft AD** and select your directory by name or Directory
   ID (`d-xxxxxxxxxx`).
4. Enter a **file system administrative username** (typically
   `Admin` or a delegated admin) and its password. The file
   system uses this account to join the domain on your behalf.
5. Pick the **Storage capacity** (32 GiB to 65 536 GiB) and
   **Throughput capacity** (8 MB/s to 2 GB/s in predefined tiers).
6. Set the **SMB encryption** level, the **daily backup window**,
   and the **maintenance window**, then create.

Behind the scenes, FSx:

- creates a **computer object** for the file system in the
  directory's `Computers` OU (or the OU you choose);
- sets up a **one-way trust** from the file system to the
  directory (so SMB clients can authenticate via Kerberos);
- exposes the file system over **SMB 2.x and 3.x** at a
  DNS name like `fs-0123456789abcdef0.corp.example.com`;
- starts writing **CloudWatch metrics** to the `AWS/FSx`
  namespace, dimensioned by `FileSystemId` and `StorageTier`.

You can verify the join by running `nltest /sc_query:<domain>` from
a Windows EC2 instance that is itself joined to the directory, or
by `Get-ADComputer -Filter * -SearchBase "OU=Computers,DC=corp,DC=example,DC=com"`
in PowerShell.

## Multi-AZ and the "FCI cluster" concept

FSx for Windows supports two deployment modes:

- **Single-AZ.** One file server in one AZ. Lower cost; if the AZ
  has an issue, you take an outage until AWS fails over.
- **Multi-AZ.** A **preferred** file server in one AZ and a
  **standby** file server in a second AZ, with **synchronous
  replication** between them. Failover is automatic and
  transparent to SMB clients. This is the FCI-style
  (File Server Cluster Instance) deployment most enterprise
  workloads want, and is what we assume in this section.

In the Multi-AZ model, the `StorageCapacity` you set is the
*total* capacity the cluster serves; you do not pay for it twice.
CloudWatch metrics for `FreeStorageCapacity` reflect the *replicated*
capacity on both file servers.

## Trusts to on-premises AD

If the plant has an on-premises AD forest (`onprem.example.local`)
and wants on-prem users to access the FSx share, the platform
team creates a **forest trust** (or an external trust) between the
on-prem forest and `corp.example.com`. AWS Managed Microsoft AD
supports:

- **One-way incoming** (on-prem trusts AWS — recommended for
  most cases).
- **One-way outgoing** (AWS trusts on-prem — only if AWS workloads
  need to authenticate to on-prem resources).
- **Two-way** (use sparingly; doubles the trust surface area).
- **Forest trust** (transitive, default for AWS Managed Microsoft
  AD).

Trusts are configured from the on-prem side using the Active
Directory Domains and Trusts snap-in; AWS provides the trust
password and direction in the directory's detail page.

## Decision flow: Managed AD vs AD Connector vs self-managed

```
Need a real Windows AD for FSx or SQL Server? ── yes ─▶ AWS Managed Microsoft AD
                          │
                          └─ no
                              │
Need to authenticate users against on-prem AD from AWS? ── yes ─▶ AD Connector
                          │
                          └─ no
                              │
                          ▼
              You almost certainly want Cognito
              or IAM Identity Center instead.
```

The other branch — **self-managed AD on EC2** — is the legacy
option. It is still valid for very specific scenarios (custom
schema extensions, very large forests, integration with software
that requires direct DC admin), but for the common "I need FSx
for Windows and a directory" case, AWS Managed Microsoft AD is
the right answer.

## The use case in section 15, restated

The plant is migrating an on-premises FCI cluster to AWS. The
migration is *hybrid*: the on-prem AD stays authoritative, and
`corp.example.com` (the AWS Managed Microsoft AD) trusts the
on-prem forest. The FSx file system joins `corp.example.com`. On-prem
users get SMB Kerberos auth to the file system via the trust.

For the **monitoring** system we are about to build, none of this
matters beyond a single fact: **the FSx file system has a
`DirectoryId`**. The monitor Lambda does *not* talk to AD at
all — it only talks to FSx and SNS. The directory is part of the
*platform*, not part of the *monitor*.

## Hands-on preview (deferred to L87)

You do not need to provision a directory to read this lecture.
Three things you can do right now:

1. **Sketch the trust diagram** for your own environment. Where
   is the source-of-truth AD? Which workloads are joined to it?
   Where would a directory connector sit?
2. **Cost-shape the decision.** AWS Managed Microsoft AD
   Standard Edition is ~$0.13/hour (~$94/month) for two DCs;
   Enterprise Edition is ~$0.40/hour (~$290/month) and adds
   larger forests, more trusts, and advanced features. If you
   only need FSx for a small file share, the platform team may
   already have a directory you can join.
3. **Run the test suite** to confirm the monitor Lambda still
   imports and tests pass with no changes:

   ```bash
   cd code/monitor_lambda
   pytest -v
   ```

The actual `CreateDirectory` call and the FSx file-system join
are in the platform-team runbook, not in section 15. The
CloudFormation template in L87 takes the **directory ID** as a
parameter (or, more typically, looks up the existing one); it
does not create the directory.

## Quiz prep

You should now be able to answer:

- What three things does AWS Managed Microsoft AD provision on
  your behalf?
- When would you pick **AD Connector** instead of **AWS Managed
  Microsoft AD**?
- Why does AWS Managed Microsoft AD require two subnets in
  different AZs?
- What does it mean for an FSx file system to be "joined" to a
  directory, and where does the join happen at the protocol
  level?
- How does the FCI / Multi-AZ deployment differ from a
  Single-AZ deployment, and which one does the section-15 use
  case assume?

## Further reading

- AWS docs: [What is AWS Managed Microsoft AD?](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_microsoft_ad.html)
- AWS docs: [Create your AWS Managed Microsoft AD directory](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/ms_ad_getting_started.html)
- AWS docs: [Joining an FSx for Windows file system to a
  Microsoft AD](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/fsx-aws-managed-ad.html)
- AWS docs: [Multi-AZ file systems](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/high-availability-multi-az.html)
- AWS docs: [When to use AWS Managed Microsoft AD vs AD
  Connector vs Simple AD](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/which_directory.html)
- L85 — FSx for Windows File Server 101
- L86 — the monitor Lambda
