# region_az_demo

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 02 (EC2 Fundamentals)
> **Companion lecture:** L06, L08

A tiny boto3 demo that shows two things from the L06 lecture:

1. Which AWS regions the current account can use, with their
   endpoints.
2. Which Availability Zones exist in the current region, and how the
   conventional AZ name (e.g. `us-east-1a`) maps to the
   account-specific AZ ID (e.g. `use1-az1`).

The whole script is stdlib + `boto3`. No third-party packages
required to run it; `moto` is only needed to run the tests.

## Files

| File | Purpose |
|---|---|
| `region_az_demo.py` | The demo. Importable functions plus a `main()` that runs end-to-end. |
| `test_region_az_demo.py` | pytest suite (16 tests) using `moto.mock_aws` and pure unit tests. |

## Run the demo

```bash
# From this directory
python region_az_demo.py
```

Optional environment variables:

- `AWS_REGION` (highest priority) — region to inspect.
- `AWS_DEFAULT_REGION` (fallback) — same idea, AWS-CLI convention.
- If neither is set, the demo defaults to `us-east-1`.

You also need AWS credentials. Any of these work:

- `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` env vars
- `aws configure` (writes `~/.aws/credentials`)
- `AWS_PROFILE` + `aws sso login`

If no credentials are configured, the demo **does not crash**. It
prints a friendly message explaining what to do, then exits 0.

Sample output (real account, `us-east-1`):

```
region_az_demo — region = us-east-1

Enabled regions visible to this account: 33
Region    | Endpoint
-----------+---------------------------
af-south-1 | ec2.af-south-1.amazonaws.com
ap-east-1  | ec2.ap-east-1.amazonaws.com
...

Availability Zones in us-east-1: 6
AZ Name | AZ ID (account-specific)
--------+-------------------------
us-east-1a | use1-az1
us-east-1b | use1-az2
us-east-1c | use1-az4
us-east-1d | use1-az5
us-east-1e | use1-az6
us-east-1f | use1-az3

AZ name -> AZ ID mapping (this account):
  us-east-1a  ->  use1-az1
  us-east-1b  ->  use1-az2
  ...
```

Note the "shuffle": `us-east-1c` maps to `use1-az4`, not
`use1-az3`. That is the L06 point — AWS randomizes the
name-to-ID mapping per account.

## Run the tests

```bash
# From this directory
python -m pytest -v
```

The tests use `moto >= 5.0` (`@mock_aws`) to stand up an in-memory
EC2 client. No real AWS account is needed. The suite has 16 tests
covering:

- `build_az_name_to_id_map` correctness (4 tests)
- `pick_default_region` precedence (4 tests)
- `render_regions_table` / `render_azs_table` (3 tests)
- `describe_regions()` returns >= 10 regions
- `describe_availability_zones()` returns AZs with both name and ID
- End-to-end pipeline: list -> map
- `main()` bails out gracefully when credentials are missing (2 tests)

## Importable helpers

The script is a module too. The functions are designed to be
imported and reused:

```python
from region_az_demo import (
    list_regions,
    list_availability_zones,
    build_az_name_to_id_map,
)

import boto3
ec2 = boto3.client("ec2", region_name="us-east-1")
regions = list_regions(ec2)
azs = list_availability_zones(ec2)
mapping = build_az_name_to_id_map(azs)
print(mapping["us-east-1a"])   # e.g. "use1-az1"
```

## Further reading

- L06 — Regions and Availability Zones (`../../lecture_scripts/L06_regions_and_azs.md`)
- L08 — Section recap (`../../lecture_scripts/L08_section_recap.md`)
- AWS: [AZ IDs and account-specific mapping](https://docs.aws.amazon.com/ram/latest/userguide/working-with-az-ids.html)
