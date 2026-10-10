# L08 — Section Recap + `region_az_demo.py`

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 02
> **Duration target:** 5:00
> **Lecture ID:** L08

## Status

Authored.

## Prereqs

- L04–L07.

## Key terms

- **Region** — a geographic AWS area, e.g. `us-east-1`.
- **Availability Zone (AZ)** — one or more data centers in a region.
- **AZ name vs AZ ID** — the conventional `us-east-1a` vs the
  per-account `use1-az1`. Same name, different ID across accounts.
- **EC2 instance type** — `<family><generation>.<size>`.
- **Shared responsibility** — AWS owns the cloud, you own what you
  put in it.

## Lecture

This is the recap lecture for section 2. We have built five
mental models in 42 minutes, and in the last five minutes I want
to make sure they are wired together and that you have a working
piece of code to play with.

**The five mental models, in one view:**

1. **The stack.** Physical hardware at the bottom. A type-1
   hypervisor (now AWS Nitro) carving it into virtual machines.
   Each EC2 instance is a VM with its own vCPUs, memory, disk,
   and network. You never see the host, and that is the
   abstraction. (L04)
2. **The responsibility split.** EC2 is IaaS, not a managed
   service. AWS owns the hardware, the hypervisor, and the
   data-center physical security. You own the guest OS, the
   patching, the scaling, the security groups, the backups, and
   every byte of data. The shared responsibility model makes
   this split explicit. (L05)
3. **The geographic model.** AWS is many regions; each region
   is many AZs. AZs in a region are connected by private
   high-bandwidth fiber. AZ names are conventional labels; AZ
   IDs are per-account physical identifiers. (L06)
4. **The instance catalog.** ~600 instance types, organized into
   families (M, T, C, R, X, I, D, P, G, Inf), generations
   (`m5` vs `m6i` vs `m7g`), and sizes (nano through 24xlarge+).
   Pick the family that matches the bottleneck, the newest
   generation available, and the smallest size your workload
   actually needs. (L07)
5. **The code.** `region_az_demo.py` exercises (3) directly
   using boto3, with a graceful bail-out when credentials are
   missing. The test suite validates the same behavior against
   mocked AWS so you can run it offline.

In section 3, we will finally launch an instance end-to-end.
You will need all five of these models in your head to do it
well, because every choice in the launch wizard — region, AZ,
AMI, instance type, security group, key pair — is one of the
concepts we covered in this section.

## Hands-on

This is the section's hands-on lecture. We walk through
`code/region_az_demo/` end-to-end.

**Step 1 — read the script.** Open
`code/region_az_demo/region_az_demo.py`. Note the structure:
three small helper functions (`list_regions`,
`list_availability_zones`, `build_az_name_to_id_map`), two
pretty-printing helpers, and a `main()` that wires them
together. The docstring at the top of the file says exactly
what it does and what dependencies it has (just `boto3` from
stdlib, no third-party packages required to *run* the demo).

**Step 2 — run it (with credentials).** If you have AWS
credentials configured, run:

```bash
cd 02_ec2_fundamentals/code/region_az_demo
python region_az_demo.py
```

You will see two tables. The first shows every region visible
to your account, with endpoints. The second shows every AZ in
your current region, with both the conventional name
(`us-east-1a`) and the account-specific ID (`use1-az1`).
Notice that the mapping is **shuffled** — `us-east-1c` might
map to `use1-az4` — exactly the L06 point.

**Step 3 — run it (without credentials).** Unset
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or just
delete `~/.aws/credentials` for the duration). Run the same
command. The script prints a friendly message explaining what
to configure, then exits 0. No stack trace. This is what we
mean by "bails out gracefully".

**Step 4 — run the tests.**

```bash
cd 02_ec2_fundamentals/code/region_az_demo
python -m pytest -v
```

The 16 tests use `moto` to stand up a fake EC2 client and
exercise the demo's behavior. They run in under three seconds
and need no AWS credentials at all. If you can read a passing
test run, you understand what the demo *should* do — the
asserts are the spec.

**Step 5 — read the test file.** Open
`test_region_az_demo.py`. Notice three test layers:
- Pure unit tests (no AWS): the mapping helper, the
  env-var precedence in `pick_default_region`, the
  pretty-printers.
- Mocked-AWS tests: `describe_regions` returns >= 10
  regions, `describe_availability_zones` returns AZs with
  name + ID, end-to-end pipeline.
- `main()` graceful-bail tests: with and without
  credentials configured, the demo exits 0 and prints a
  friendly message.

When you build your own boto3 scripts in later sections, copy
this structure. Pure unit tests for pure logic. `@mock_aws`
tests for any code that talks to AWS. A separate test class
for the `main()` entry point that proves it does not crash on
a fresh laptop.

## Quiz prep

- In one sentence each, summarize L04, L05, L06, and L07.
- Run `python region_az_demo.py` and explain the AZ name ->
  AZ ID mapping. Why is it shuffled? (L06)
- Look at the `test_region_az_demo.py` test file. Which tests
  need real AWS credentials, and which do not? (Hint: count
  the `@mock_aws` decorators.)
- What does `pick_default_region()` return when neither
  `AWS_REGION` nor `AWS_DEFAULT_REGION` is set?

## Further reading

- `code/region_az_demo/README.md` — run instructions for the
  demo.
- `../../quizzes/section_2.md` — 10-question quiz for the
  section (pass bar 7/10).
- L06 lecture script — the AZ-name-vs-AZ-ID point in detail.

## What's next

Section 3 — **Creating an EC2 instance end-to-end** (L09–L18).
We finally open the EC2 launch wizard and start filling in
real fields: AMI, instance type, network, storage, security
groups, key pairs, and user data. Every one of those fields
hooks back to a concept from this section.