"""
alb_create.py — create an Application Load Balancer with a target group,
a default listener, and two rules.

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 7 — Application Load Balancer

The script exposes a single function ``create_alb_and_rules`` that takes
the VPC, two subnets in two AZs, and a security group, and returns the
four ARNs the caller is most likely to need:

* ``alb_arn``
* ``target_group_arn``
* ``listener_arn``
* ``api_rule_arn``

The two rules on the listener are:

* Priority 10 — path-pattern ``/api/*`` → forward to the target group.
* Default action — fixed response 404 with an HTML body.

The function is boto3-only. Every call is mocked by ``moto>=5.0`` in
``test_alb_create.py`` so the tests can verify the ALB shape without
touching AWS.

Usage (against real AWS):

    python alb_create.py
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import boto3


# ---------------------------------------------------------------------------
# Defaults — overridable via environment variables so the same script works
# in the console walkthrough, the unit tests, and a real AWS account.
# ---------------------------------------------------------------------------
DEFAULT_REGION = "us-east-1"
DEFAULT_ALB_NAME = "alb-demo"
DEFAULT_TG_NAME = "tg-alb-demo"


def _elbv2_client(region_name: Optional[str] = None) -> Any:
    """Return a boto3 ELBv2 client.

    Using a thin wrapper makes the function trivially monkey-patchable in
    tests if we ever need to inject a different client.
    """
    return boto3.client(
        "elbv2",
        region_name=region_name or os.environ.get("AWS_REGION", DEFAULT_REGION),
    )


def create_alb_and_rules(
    vpc_id: str,
    subnet_ids: List[str],
    security_group_id: str,
    *,
    alb_name: str = DEFAULT_ALB_NAME,
    tg_name: str = DEFAULT_TG_NAME,
    region_name: Optional[str] = None,
    client: Optional[Any] = None,
) -> Dict[str, str]:
    """Create the ALB, target group, listener, and rules.

    Parameters
    ----------
    vpc_id:
        The VPC to deploy the load balancer and target group into.
    subnet_ids:
        **At least two** subnet IDs in **two different AZs**. AWS
        refuses to create an ALB that lives in only one AZ.
    security_group_id:
        Security group ID to attach to the ALB ENIs. Must allow
        inbound HTTP (port 80) from the desired source.
    alb_name, tg_name:
        Names for the load balancer and target group. Must be
        unique within the AWS account and region.
    region_name:
        Optional region override. Defaults to ``AWS_REGION`` env var,
        then ``us-east-1``.
    client:
        Optional boto3 ELBv2 client. Used by tests to inject a
        moto-mocked client.

    Returns
    -------
    dict
        ``alb_arn``, ``target_group_arn``, ``listener_arn``,
        ``api_rule_arn``.
    """
    if len(subnet_ids) < 2:
        raise ValueError(
            "ALB requires subnets in at least two AZs; got "
            f"{len(subnet_ids)} subnet(s)."
        )

    elbv2 = client or _elbv2_client(region_name)

    # ------------------------------------------------------------------
    # Step 1 — Target group.
    # ------------------------------------------------------------------
    tg_resp = elbv2.create_target_group(
        Name=tg_name,
        Protocol="HTTP",
        Port=80,
        VpcId=vpc_id,
        TargetType="instance",
        HealthCheckProtocol="HTTP",
        HealthCheckPath="/health",
        HealthCheckIntervalSeconds=30,
        HealthCheckTimeoutSeconds=5,
        HealthyThresholdCount=2,
        UnhealthyThresholdCount=2,
        Matcher={"HttpCode": "200"},
    )
    target_group_arn = tg_resp["TargetGroups"][0]["TargetGroupArn"]

    # ------------------------------------------------------------------
    # Step 2 — Load balancer.
    # ------------------------------------------------------------------
    alb_resp = elbv2.create_load_balancer(
        Name=alb_name,
        Type="application",                  # ALB, not NLB / GWLB
        Scheme="internet-facing",            # public, not internal
        IpAddressType="ipv4",
        Subnets=subnet_ids,                  # must be 2+ in 2 AZs
        SecurityGroups=[security_group_id],
    )
    alb_arn = alb_resp["LoadBalancers"][0]["LoadBalancerArn"]

    # ------------------------------------------------------------------
    # Step 3 — Default listener.
    # The default action is a fixed 404 — anything that doesn't match a
    # higher-priority rule gets the 404 response (see L33).
    # ------------------------------------------------------------------
    listener_resp = elbv2.create_listener(
        LoadBalancerArn=alb_arn,
        Protocol="HTTP",
        Port=80,
        DefaultActions=[
            {
                "Type": "fixed-response",
                "FixedResponseConfig": {
                    "StatusCode": "404",
                    "ContentType": "text/html",
                    "MessageBody": "<h1>Not Found</h1>",
                },
            }
        ],
    )
    listener_arn = listener_resp["Listeners"][0]["ListenerArn"]

    # ------------------------------------------------------------------
    # Step 4 — Priority-10 rule that forwards /api/* to the target group.
    # ------------------------------------------------------------------
    rule_resp = elbv2.create_rule(
        ListenerArn=listener_arn,
        Priority=10,
        Conditions=[
            {"Field": "path-pattern", "Values": ["/api/*"]},
        ],
        Actions=[
            {"Type": "forward", "TargetGroupArn": target_group_arn},
        ],
    )
    api_rule_arn = rule_resp["Rules"][0]["RuleArn"]

    return {
        "alb_arn": alb_arn,
        "target_group_arn": target_group_arn,
        "listener_arn": listener_arn,
        "api_rule_arn": api_rule_arn,
    }


# ---------------------------------------------------------------------------
# CLI entrypoint — useful for the console walkthrough in L32 / L35.
# Reads the VPC, subnets, and security group from environment variables so
# the same script works in CI, locally, or against a real AWS account.
# ---------------------------------------------------------------------------
def _cli() -> Dict[str, str]:
    vpc_id = os.environ["VPC_ID"]
    subnet_ids = os.environ["SUBNET_IDS"].split(",")
    security_group_id = os.environ["SECURITY_GROUP_ID"]

    return create_alb_and_rules(
        vpc_id=vpc_id,
        subnet_ids=subnet_ids,
        security_group_id=security_group_id,
        region_name=os.environ.get("AWS_REGION", DEFAULT_REGION),
    )


if __name__ == "__main__":
    import json

    result = _cli()
    print(json.dumps(result, indent=2))