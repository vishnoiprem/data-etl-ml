# L37 — GWLB Hands-On + `gwlb_create.py` + tests

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 08
> **Duration target:** 12:00
> **Lecture ID:** L37

## Status

Authored.

## Prereqs

- L36 (GWLB theory).
- L30 — `nlb_create.py` (you've seen the NLB equivalent).
- L35 — `alb_create.py` (you've seen the ALB equivalent).

## Key terms

- **`elbv2.create_load_balancer(..., Type='gateway', ...)`** — the
  one API call that creates a GWLB.
- **`elbv2.create_target_group(..., Protocol='GENEVE', Port=6081, ...)`**
  — the target group whose instances will receive the
  GENEVE-encapsulated frames.
- **`HealthCheckProtocol='HTTP', HealthCheckPath='/health'`** — the
  appliance's management endpoint that the GWLB polls to decide
  whether to route new flows to it.
- **moto `mock_aws`** — in-memory AWS used by the test suite; lets
  us run pytest offline.

## Lecture

Welcome back. In L36 we covered the theory. In L37 we build a
Gateway Load Balancer end-to-end with boto3 and then prove the
shape of the result with three pytest tests.

The working artifact is in
`08_load_balancing_gwlb/code/gwlb_create/`:

```
gwlb_create/
├── gwlb_create.py          # the boto3 module
├── test_gwlb_create.py     # 3 pytest tests with @mock_aws
└── README.md               # the appliance-vendor pattern
```

Let me walk you through the script.

### The API surface

Just like NLB and ALB, GWLB lives in the same **`elbv2` service** —
there is no separate `elbv2-gateway` client. The differences are
purely in the parameters:

- `Type='gateway'` on `create_load_balancer` (instead of
  `'application'` or `'network'`).
- `Protocol='GENEVE'` and `Port=6081` on `create_target_group`
  (instead of `'HTTP'` / `'HTTPS'` / `'TCP'` / `'UDP'`).
- The `create_listener` call is sparser: no `Protocol`, no `Port`,
  no `SslPolicy` — GENEVE/6081 is fixed by the LB type.

That last point surprises people. Real AWS will reject any attempt
to set `Protocol` or `Port` on a gateway listener. The GWLB listener
*is* GENEVE/6081 by construction.

### `create_gwlb(...)`

The function takes five named parameters:

- `name` — the LB name (and the target group is named `<name>-tg`).
- `subnet_ids` — exactly two subnets in two different AZs.
- `vpc_id` — the VPC that owns the target group.
- `health_check_path` — defaults to `/health`.
- `region_name` — defaults to `us-east-1`.

It also accepts an optional pre-built `client` (used by the tests so
they can pass a `moto`-backed client without re-creating one).

The function performs three API calls in order:

1. `create_target_group(Name=tg_name, Protocol='GENEVE', Port=6081,
   VpcId=vpc_id, TargetType='instance',
   HealthCheckProtocol='HTTP', HealthCheckPath=health_check_path,
   HealthCheckPort='80')`.
2. `create_load_balancer(Name=name, Type='gateway',
   Subnets=subnet_ids)`.
3. `create_listener(LoadBalancerArn=lb_arn,
   DefaultActions=[{'Type':'forward','TargetGroupArn':tg_arn}])`.

It returns a `GwlbResult` dataclass with the three ARNs. The
dataclass has an `as_dict()` method that returns a plain
`{'LoadBalancerArn': ..., 'TargetGroupArn': ..., 'ListenerArn': ...}`
dict, suitable for printing or serialising.

### The tests

`test_gwlb_create.py` uses `moto.mock_aws` to spin up a fake AWS
account in memory. The `aws_env` fixture creates a VPC and two
subnets in two different AZs, then calls `create_gwlb(...)` and
hands the returned result + the `elbv2` client to the tests.

Three tests, all of which must pass:

- `test_gwlb_type_is_gateway` — describes the load balancer by
  ARN and asserts `Type == 'gateway'`, and that the LB is deployed
  in exactly the two subnets we passed in.
- `test_target_group_protocol_geneve` — describes the target
  group and asserts `Protocol == 'GENEVE'`, `Port == 6081`,
  `HealthCheckProtocol == 'HTTP'`, `HealthCheckPath == '/health'`,
  and that the TG is in our VPC.
- `test_listener_forwards_to_target_group` — describes the listener
  and asserts that there is exactly one default action, of type
  `forward`, pointing at our target group ARN. The protocol is
  either `''` (moto's representation) or `'GENEVE'` (real AWS).

### Running the suite

```bash
cd 08_load_balancing_gwlb/code/gwlb_create
python -m pytest test_gwlb_create.py -v
```

You should see three green dots. Total run time is about 2-3
seconds because `moto` is in-memory.

### What this script does **not** do

For the sake of staying within 12 minutes I have left three things
out of the demo:

- **Registering appliance targets** — you'd normally call
  `register_targets(TargetGroupArn=..., Targets=[{'Id': 'i-aaaa'}])`
  after the target group is created. We just create an empty
  target group.
- **VPC endpoint service** — the production way to expose a GWLB
  to other VPCs. Described in L36; would be its own lecture.
- **Cross-AZ load balancing** — the demo creates subnets in two
  AZs but does not set `CrossZoneLoadBalancing`. For GWLB,
  cross-zone is enabled by default at the GWLB level (since the
  GWLB itself spans two AZs), unlike NLB.

## Hands-on

The hands-on for this lecture is running the test suite and reading
through `gwlb_create.py`. The full appliance deployment (with
marketplace AMI, PrivateLink service, cross-VPC consumer) is out of
scope and is recommended further study in L38.

## Quiz prep

- A GWLB is created with `elbv2.create_load_balancer` and
  `Type='gateway'`.
- A GWLB target group is created with `Protocol='GENEVE'`,
  `Port=6081`. Health checks are typically HTTP on `/health`.
- A GWLB is always deployed across **two subnets in two AZs**.
- The `create_listener` call for a GWLB **does not specify
  Protocol or Port** — GENEVE/6081 is fixed.
- The `create_listener` `DefaultActions` is a single `forward`
  action pointing at the target group ARN.

## Further reading

- AWS Docs — *Create a Gateway Load Balancer.*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/create-gateway-load-balancer.html>
- boto3 — *ElasticLoadBalancingv2 client reference.*
  <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html>
- `moto` — *Gateway Load Balancer support.*
  <https://docs.getmoto.org/en/latest/docs/services/elbv2.html>