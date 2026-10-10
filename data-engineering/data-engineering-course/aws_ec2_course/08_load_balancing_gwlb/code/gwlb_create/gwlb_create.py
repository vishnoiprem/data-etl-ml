"""gwlb_create.py — Create an AWS Gateway Load Balancer (GWLB) with boto3.

> Author: Prem Vishnoi <prem.vishnoi@example.com>
> Section: 08 — Gateway Load Balancer + Course Wrap-up
> Lecture: L37 — GWLB Hands-On

The Gateway Load Balancer (GWLB) is a Layer-3 transparent appliance
insertion service. It uses the GENEVE protocol on UDP port 6081 to
encapsulate customer traffic and forward it to a fleet of third-party
virtual appliances (firewalls, IDS/IPS, NAT, etc.) running in EC2.

This module exposes a single ``create_gwlb(...)`` function that
provisions the three required pieces in order:

  1. A target group of type ``GENEVE`` on port 6081.
  2. The gateway load balancer itself (across two subnets in different AZs).
  3. A single GENEVE listener that defaults to forwarding to the target group.

The function returns a dict with the ARNs of the created resources so
callers (and tests) can inspect them.

Notes
-----
* In real AWS, a GWLB listener is fixed to GENEVE/6081 — you cannot
  override the protocol or port. ``boto3`` therefore omits both
  parameters when creating the listener; GENEVE/6081 is implied by
  the gateway load balancer type.
* The target group uses HTTP health checks on ``/health``. Real GWLB
  appliances typically expose a management HTTP endpoint that
  responds 200 OK when the appliance is healthy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import boto3


@dataclass
class GwlbResult:
    """Container for the three ARNs produced by :func:`create_gwlb`."""

    load_balancer_arn: str
    target_group_arn: str
    listener_arn: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "LoadBalancerArn": self.load_balancer_arn,
            "TargetGroupArn": self.target_group_arn,
            "ListenerArn": self.listener_arn,
        }


def create_gwlb(
    name: str,
    subnet_ids: List[str],
    vpc_id: str,
    target_group_name: Optional[str] = None,
    health_check_path: str = "/health",
    region_name: str = "us-east-1",
    client: Optional["boto3.session.Session"] = None,
) -> GwlbResult:
    """Create a Gateway Load Balancer, its target group, and its listener.

    Parameters
    ----------
    name:
        Name for the gateway load balancer. The target group is named
        ``<name>-tg`` unless ``target_group_name`` is provided.
    subnet_ids:
        Exactly two subnet IDs in two different Availability Zones.
        A gateway load balancer is always deployed across two AZs.
    vpc_id:
        VPC that owns the target group and the subnets.
    target_group_name:
        Optional override for the target group name. Defaults to
        ``<name>-tg`` (max 32 chars, alphanumeric + hyphens).
    health_check_path:
        HTTP path used for target health checks. Defaults to ``/health``.
    region_name:
        AWS region. Defaults to ``us-east-1``.
    client:
        Optional pre-built boto3 ``elbv2`` client. Useful for tests
        that run under ``moto.mock_aws``.

    Returns
    -------
    GwlbResult
        A dataclass with ``load_balancer_arn``, ``target_group_arn``,
        and ``listener_arn``.
    """
    if len(subnet_ids) != 2:
        raise ValueError(
            "A Gateway Load Balancer requires exactly two subnets "
            "in two different Availability Zones."
        )

    elbv2 = client or boto3.client("elbv2", region_name=region_name)

    tg_name = target_group_name or f"{name}-tg"
    if len(tg_name) > 32:
        # AWS caps target group names at 32 characters.
        tg_name = tg_name[:32]

    # ── 1. Target group (GENEVE / 6081) ────────────────────────────────
    tg_response = elbv2.create_target_group(
        Name=tg_name,
        Protocol="GENEVE",
        Port=6081,
        VpcId=vpc_id,
        TargetType="instance",
        HealthCheckProtocol="HTTP",
        HealthCheckPath=health_check_path,
        HealthCheckPort="80",
    )
    target_group_arn: str = tg_response["TargetGroups"][0]["TargetGroupArn"]

    # ── 2. Gateway Load Balancer (two subnets) ─────────────────────────
    gwlb_response = elbv2.create_load_balancer(
        Name=name,
        Type="gateway",
        Subnets=subnet_ids,
    )
    load_balancer_arn: str = gwlb_response["LoadBalancers"][0][
        "LoadBalancerArn"
    ]

    # ── 3. Listener (GENEVE is implied by LB type) ─────────────────────
    # In real AWS a GWLB listener is fixed to GENEVE/6081; passing Port
    # or Protocol is rejected. The DefaultAction is a single forward.
    listener_response = elbv2.create_listener(
        LoadBalancerArn=load_balancer_arn,
        DefaultActions=[
            {
                "Type": "forward",
                "TargetGroupArn": target_group_arn,
            }
        ],
    )
    listener_arn: str = listener_response["Listeners"][0]["ListenerArn"]

    return GwlbResult(
        load_balancer_arn=load_balancer_arn,
        target_group_arn=target_group_arn,
        listener_arn=listener_arn,
    )


if __name__ == "__main__":
    # Manual smoke run — requires real (or moto) AWS credentials and
    # two real subnets. See the README for the suggested flow.
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="demo-gwlb")
    parser.add_argument("--vpc-id", required=True)
    parser.add_argument("--subnet-a", required=True)
    parser.add_argument("--subnet-b", required=True)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    result = create_gwlb(
        name=args.name,
        subnet_ids=[args.subnet_a, args.subnet_b],
        vpc_id=args.vpc_id,
        region_name=args.region,
    )
    print(result.as_dict())
