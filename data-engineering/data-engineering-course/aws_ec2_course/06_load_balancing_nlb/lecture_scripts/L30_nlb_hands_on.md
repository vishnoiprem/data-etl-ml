# L30 — NLB Hands-On + `nlb_create.py` + tests

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 06
> **Duration target:** 10:00
> **Lecture ID:** L30

## Status

Authored.

## Prereqs

- L27, L28, L29. You should know what a target group is, what a
  health check does, and why an NLB is the right choice for TCP
  workloads and static IPs.

## Key terms

- **boto3 `elbv2` client** — the unified client for all three AWS
  load-balancer flavours (ALB, NLB, GWLB). The same `create_listener`
  call works for any of them; the differences are in the
  `Type='network' | 'application' | 'gateway'` argument to
  `create_load_balancer`.
- **moto `mock_aws` decorator** — pytest fixture / decorator from
  the `moto` library that stubs out every AWS service for the
  duration of the test. Lets you assert boto3 behaviour without
  making real AWS calls.

## Lecture

The whole point of this section is the small but production-shaped
script at `code/nlb_create/nlb_create.py`. It is roughly 80 lines of
Python and creates the three resources an NLB needs. We will walk
through it top to bottom, then run the tests.

The script is built around a single function,
`create_nlb_with_target_group`, which returns a dictionary with the
NLB DNS name and the target group ARN. This is the unit you would
import in a real system — for example, a CloudFormation custom
resource, or a deploy script.

```python
def create_nlb_with_target_group(
    client: "botocore.client.BaseClient",
    nlb_name: str,
    vpc_id: str,
    subnet_ids: list[str],
    tg_name: str | None = None,
    target_port: int = 80,
    listener_port: int = 80,
    health_check_path: str = "/health",
) -> dict[str, str]:
```

The first API call is `create_target_group`. We give it a name, the
target type (`instance`, `ip`, or `lambda`; we use `instance` because
our backend is EC2), the protocol (`TCP`, since we are building an
NLB), the port, and the VPC. We also pass a health-check block. Even
though the listener is TCP, the health check is HTTP on `/health` —
this is the L28 pattern: the load balancer does pass-through TCP, but
the target group uses HTTP so we get a real liveness signal from the
application.

```python
tg = client.create_target_group(
    Name=tg_name or f"{nlb_name}-tg",
    Protocol="TCP",
    Port=target_port,
    VpcId=vpc_id,
    TargetType="instance",
    HealthCheckProtocol="HTTP",
    HealthCheckPath=health_check_path,
    HealthCheckIntervalSeconds=30,
    HealthyThresholdCount=3,
    UnhealthyThresholdCount=3,
)
```

The second API call is `create_load_balancer`. The two arguments that
matter for an NLB are `Type='network'` and `Scheme='internet-facing'`
(or `'internal'`). The `Subnets` list is what gives you multi-AZ;
each subnet becomes one load-balancer node, and you should always
pass at least two (one per AZ).

```python
nlb = client.create_load_balancer(
    Name=nlb_name,
    Type="network",
    Scheme="internet-facing",
    Subnets=subnet_ids,
)
```

The third API call is `create_listener`. A listener is what ties a
port on the load balancer to a target group. The default action is
`Type='forward'` with a `TargetGroupArn` pointing at the target group
we just created. That is it. With three boto3 calls you have a
production-shaped NLB.

```python
listener = client.create_listener(
    LoadBalancerArn=nlb_arn,
    Protocol="TCP",
    Port=listener_port,
    DefaultActions=[{
        "Type": "forward",
        "TargetGroupArn": tg_arn,
    }],
)
```

After these three calls, the function returns
`{"dns_name": ..., "target_group_arn": ...}`. The DNS name is the
"stable endpoint" from L27. You point your application's DNS at it
(CNAME for a subdomain, A records using the static IPs for an Apex
domain) and you are done.

The script's `main()` function is the runnable example. It prints
the DNS name and exits. The `if __name__ == "__main__":` block means
you can run it with `python nlb_create.py` to print the DNS name
from a moto-mocked environment, or import the function in your own
deploy script to do something more interesting.

## Hands-on

```bash
cd 06_load_balancing_nlb/code/nlb_create
python -m pytest test_nlb_create.py -v
```

You should see four tests pass. Each test uses `@mock_aws` to stub
ELBv2, then asserts one of the four properties we care about: target
group ARN format, NLB DNS name format, listener default action, and
NLB type.

To run it for real (not mocked), you need a VPC with at least two
public subnets in different AZs. See `code/nlb_create/README.md` for
the IAM permissions and the boto3 flag reference.

## Quiz prep

- The boto3 client for all load balancers is `boto3.client("elbv2",
  region_name=...)`.
- The three API calls in order are: `create_target_group`,
  `create_load_balancer`, `create_listener`.
- The NLB is created with `Type="network"` and
  `Scheme="internet-facing"` (or `"internal"`).
- Multi-AZ is achieved by passing **at least two subnets** in
  different AZs to `create_load_balancer`.
- The listener's `DefaultActions` is a list of one dict with
  `Type="forward"` and `TargetGroupArn=...`.
- The NLB's DNS name is the **stable endpoint** clients hit; the
  instances behind it can be replaced at will.

## Further reading

- boto3 docs — `ElasticLoadBalancingv2.Client.create_load_balancer`
  <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_load_balancer>
- boto3 docs — `ElasticLoadBalancingv2.Client.create_target_group`
  <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_target_group>
- moto docs — `mock_aws` decorator
  <https://docs.getmoto.org/en/latest/docs/configuration.html>
