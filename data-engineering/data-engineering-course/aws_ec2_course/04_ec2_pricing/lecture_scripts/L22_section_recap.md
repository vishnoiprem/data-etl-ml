# L22 — Section Recap + `pricing_calc.py` Walkthrough

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 04
> **Duration target:** 8:00
> **Lecture ID:** L22

## Status

Authored.

## Prereqs

- L19, L20, L21.

## Key terms

- **Pricing calculator** — a tool that takes an instance type, hours, and a model, and returns a dollar estimate. Our `pricing_calc.py` is a stdlib-only Python module.
- **Side-by-side comparison** — printing a table of estimated monthly cost for the same workload under each of the five pricing models.
- **Effective discount** — `(1 - model_cost / on_demand_cost) * 100`, expressed as a percentage.

## Lecture

In L19 we covered the five EC2 pricing models at a high level. In L20 we went deep on the three non-spot models: on-demand, Reserved Instances, and Savings Plans. In L21 we covered spot end to end, including interruption behavior and the workload types that fit it. The recap today is short and practical: take what you know and put numbers on it.

The artifact is `code/pricing_calc.py`. It is a pure-Python module — no boto3, no requests, no AWS dependency at all. It ships with a `PRICING` dict containing illustrative 2026 hourly rates for five instance types in us-east-1, and it exposes five functions:

- `on_demand(instance_type, hours)` — straight multiply.
- `reserved(instance_type, hours, term_years=1, payment="no_upfront")` — applies a discount based on term and payment option.
- `savings_plan(instance_type, hours, plan_type="compute")` — applies ~27% off for Compute Savings Plans.
- `spot(instance_type, hours, spot_price=None)` — uses the passed spot price, or 70% of on-demand if not given.
- `estimate_monthly(instance_type, hours_per_month=730, model="on_demand")` — a convenience wrapper that picks the right function.

The discount structure in the module is the actual point of the exercise:

| Model | Discount vs on-demand |
|---|---|
| On-demand | 0% |
| Reserved, 1y, no upfront | ~40% |
| Reserved, 3y, all upfront | ~60% |
| Savings Plan (Compute, 3y) | ~27% |
| Savings Plan (EC2 Instance, 3y) | ~37% |
| Spot (default) | ~70% |

These are illustrative numbers — real AWS discounts vary by instance family, region, and term, and the `pricing` API (which `pricing_calc.py` is designed to be extended with) is the source of truth.

The recap walkthrough is straightforward:

1. Run `python code/pricing_calc.py` from the section root. It prints a side-by-side comparison for `t3.micro` at 730 hours/month.
2. Open the file and change the instance type in `main()` to something more interesting (`m5.large`, `c5.xlarge`, `r5.large`) and re-run. Notice how the absolute dollar difference between models scales with the hourly rate.
3. Run the tests: `pytest code/test_pricing_calc.py -v`. All six should pass. They are written to test the *direction* of the discounts (reserved is cheaper than on-demand; spot is cheaper than on-demand; the override price is honored) and the *boundaries* (unknown instance type raises).
4. The tests do not check the exact discount percentages. AWS changes them; the calculator uses sensible defaults; the *direction* is what matters.

After this recap you should be able to:

- Pick a pricing model for a workload in under a minute.
- Estimate the monthly cost for a single instance type under each model.
- Explain why a workload is or is not a good fit for spot.
- Read the AWS pricing page and the Savings Plans console without being confused by the terms.

Section 5 (Managing EC2) starts at L23 with stop, start, resize, and terminate.

## Hands-on

Walk through `code/pricing_calc.py`:

1. Open `code/pricing_calc.py` and read the `PRICING` dict and the five functions.
2. From a terminal at the section root, run `python code/pricing_calc.py`. You should see a table of monthly costs for `t3.micro` at 730 hours under each model.
3. Edit `main()` to compare a different instance type (suggestion: `m5.large` or `c5.xlarge`). Re-run.
4. Run `pytest code/test_pricing_calc.py -v` and confirm all six tests pass.
5. Optional: write your own scenario — e.g., a workload that runs 8 hours/day, 5 days/week — and use `estimate_monthly` to compare. Notice that spot and Savings Plans still come out cheaper even at part-time utilization.

## Quiz prep

- What does `pricing_calc.py` use as the default spot price if you do not pass one?
- Roughly what is the discount of a 3-year Compute Savings Plan versus on-demand in the calculator?
- What function would you call to estimate a 24/7 workload's monthly cost under a 3-year reserved instance?
- How would you extend the calculator to use real AWS prices?
- If the calculator returns $30 for on-demand and $9 for spot, what is the effective discount?

## Further reading

- `code/README.md` — extending the calculator with the real `pricing` API.
- AWS Pricing API reference — https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-pelong.html
- AWS Pricing Calculator (web) — https://calculator.aws/
