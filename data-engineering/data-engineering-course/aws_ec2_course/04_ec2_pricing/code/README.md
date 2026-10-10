# `code/` — pricing_calc

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

This directory contains `pricing_calc.py`, a stdlib-only EC2 pricing calculator that illustrates the discount structure of the five EC2 pricing models covered in Section 4.

## Files

- `pricing_calc.py` — the calculator module. Run as a script to print a side-by-side comparison.
- `test_pricing_calc.py` — six pytest tests covering the direction of the discounts, the spot-price override, the convenience wrapper, and error handling for unknown instance types.

## Data source

The `PRICING` dict at the top of `pricing_calc.py` contains **illustrative 2026 us-east-1 Linux on-demand hourly rates** for five instance types:

| Instance type | USD/hour |
|---|---|
| t3.micro  | 0.0104 |
| t3.small  | 0.0208 |
| m5.large  | 0.0960 |
| c5.xlarge | 0.1920 |
| r5.large  | 0.1260 |

These numbers are reasonable for 2026 us-east-1 but are not authoritative. AWS changes them periodically and the real price varies by region, OS, and tenancy. **Do not use this calculator for actual billing.**

The `DISCOUNTS` dict captures the standard discount ranges (Reserved Instances and Savings Plans) and a default 70% discount for Spot. They are also illustrative and are the source of truth only for the *shape* of the discount — that reserved is bigger than savings plans which is bigger than on-demand, that spot is the biggest discount but is interruptible.

## How to run

```bash
cd 04_ec2_pricing/code
python pricing_calc.py                # prints comparison for t3.micro @ 730h
python -m pytest test_pricing_calc.py -v   # all six tests should pass
```

The tests do not pin exact discount percentages — they pin the *direction* of the discount (reserved < on-demand, spot < on-demand) and the *boundaries* (unknown instance type raises). That keeps the test suite stable when AWS changes the numbers.

## Extending with the real AWS Pricing API

The calculator is deliberately offline so that the section runs without AWS credentials. To wire it up to real prices, add a function that calls the `pricing` API via boto3 and updates `PRICING` at runtime:

```python
import boto3

def load_pricing_from_aws(region: str = "us-east-1") -> dict[str, float]:
    """Fetch on-demand prices for our five instance types from the pricing API."""
    client = boto3.client("pricing", region_name="us-east-1")  # pricing API is only in us-east-1
    out: dict[str, float] = {}
    for instance_type in PRICING:
        response = client.get_products(
            ServiceCode="AmazonEC2",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                {"Type": "TERM_MATCH", "Field": "location",      "Value": "US East (N. Virginia)"},
                {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                {"Type": "TERM_MATCH", "Field": "tenancy",       "Value": "Shared"},
                {"Type": "TERM_MATCH", "Field": "preInstalledSw","Value": "NA"},
                {"Type": "TERM_MATCH", "Field": "capacitystatus","Value": "Used"},
            ],
            MaxResults=1,
        )
        # parse response['PriceList'][0] (JSON string) for the OnDemand price
        # ... and put it into `out[instance_type]`
    return out
```

Then call `PRICING.update(load_pricing_from_aws())` at the top of `main()` and the rest of the calculator keeps working unchanged.

For Reserved Instance and Savings Plan discounts, the `pricing` API exposes the public on-demand rate and the discounted rate for each term. The `Savings Plans` console page lists current rates. Update `DISCOUNTS` with the same pattern.

The `pricing` API only has `us-east-1` as an endpoint regardless of where the prices are for — that is a quirk of the service, not a bug in the wrapper.

## Limitations

- No support for Windows, RHEL, or other paid OS surcharges.
- No support for dedicated tenancy or Dedicated Hosts.
- No support for the Capacity Blocks feature for short-term ML/HPC reservation.
- No regional variation — every region uses the same `PRICING` table.
- Spot price is a constant fraction of on-demand by default. Real spot prices are time-varying; for real workloads, query the `ec2` API's `describe_spot_price_history` instead.
