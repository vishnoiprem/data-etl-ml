"""Create a Network Load Balancer, target group, and TCP listener.

This is the working demo for the AWS EC2 + Load Balancing course,
Section 6 (L27-L30). It wraps the three boto3 calls you need to
stand up a production-shaped NLB end-to-end:

    1. create_target_group  (TCP/80, HTTP health check on /health)
    2. create_load_balancer  (Type=network, Scheme=internet-facing,
                              one node per AZ via Subnets)
    3. create_listener       (TCP/80 forwards to the target group)

The default health-check settings are intentionally chosen to match
L28's lecture defaults (30s interval, 3 healthy / 3 unhealthy
thresholds) so the unit tests can assert them.

Usage (real AWS):

    export AWS_REGION=us-east-1
    python nlb_create.py \\
        --nlb-name demo-nlb \\
        --vpc-id vpc-0123456789abcdef0 \\
        --subnet-ids subnet-aaa subnet-bbb \\
        --instance-ids i-aaa i-bbb

The script will print the NLB DNS name. Use that DNS name as the
CNAME for your application.

Usage (offline, mocked):

    python -m pytest test_nlb_create.py -v

Required IAM permissions (least-privilege):

    elasticloadbalancing:CreateTargetGroup
    elasticloadbalancing:CreateLoadBalancer
    elasticloadbalancing:CreateListener
    elasticloadbalancing:RegisterTargets
    elasticloadbalancing:DescribeTargetGroups
    elasticloadbalancing:DescribeLoadBalancers
    elasticloadbalancing:DescribeListeners

on resource arn:aws:elasticloadbalancing:<region>:<account>:*
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any, Optional

import boto3

LOG = logging.getLogger("ec2_course.nlb")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── helpers ────────────────────────────────────────────────────────────
def create_target_group(
    client: Any,
    name: str,
    vpc_id: str,
    *,
    protocol: str = "TCP",
    port: int = 80,
    target_type: str = "instance",
    health_check_protocol: str = "HTTP",
    health_check_path: str = "/health",
    health_check_interval_seconds: int = 30,
    healthy_threshold_count: int = 3,
    unhealthy_threshold_count: int = 3,
) -> str:
    """Create an NLB target group. Returns the TargetGroupArn."""
    resp = client.create_target_group(
        Name=name,
        Protocol=protocol,
        Port=port,
        VpcId=vpc_id,
        TargetType=target_type,
        HealthCheckProtocol=health_check_protocol,
        HealthCheckPath=health_check_path,
        HealthCheckIntervalSeconds=health_check_interval_seconds,
        HealthyThresholdCount=healthy_threshold_count,
        UnhealthyThresholdCount=unhealthy_threshold_count,
    )
    tg_arn = resp["TargetGroups"][0]["TargetGroupArn"]
    LOG.info("created target group name=%s arn=%s", name, tg_arn)
    return tg_arn


def create_nlb(
    client: Any,
    name: str,
    subnet_ids: list[str],
    *,
    scheme: str = "internet-facing",
    nlb_type: str = "network",
) -> str:
    """Create a Network Load Balancer. Returns the LoadBalancerArn."""
    resp = client.create_load_balancer(
        Name=name,
        Type=nlb_type,
        Scheme=scheme,
        Subnets=subnet_ids,
    )
    nlb_arn = resp["LoadBalancers"][0]["LoadBalancerArn"]
    LOG.info("created NLB name=%s arn=%s", name, nlb_arn)
    return nlb_arn


def create_listener(
    client: Any,
    load_balancer_arn: str,
    target_group_arn: str,
    *,
    protocol: str = "TCP",
    port: int = 80,
) -> str:
    """Create a TCP listener that forwards to the target group. Returns ListenerArn."""
    resp = client.create_listener(
        LoadBalancerArn=load_balancer_arn,
        Protocol=protocol,
        Port=port,
        DefaultActions=[{
            "Type": "forward",
            "TargetGroupArn": target_group_arn,
        }],
    )
    listener_arn = resp["Listeners"][0]["ListenerArn"]
    LOG.info("created listener arn=%s port=%s", listener_arn, port)
    return listener_arn


def register_targets(
    client: Any,
    target_group_arn: str,
    instance_ids: list[str],
) -> None:
    """Register EC2 instance IDs with the target group. No-op if list is empty."""
    if not instance_ids:
        LOG.info("no targets to register, skipping register_targets")
        return
    client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{"Id": iid} for iid in instance_ids],
    )
    LOG.info("registered %d target(s) with %s", len(instance_ids), target_group_arn)


def create_nlb_with_target_group(
    client: Any,
    nlb_name: str,
    vpc_id: str,
    subnet_ids: list[str],
    *,
    tg_name: Optional[str] = None,
    target_port: int = 80,
    listener_port: int = 80,
    scheme: str = "internet-facing",
    instance_ids: Optional[list[str]] = None,
    health_check_path: str = "/health",
) -> dict[str, str]:
    """End-to-end: target group + NLB + listener + (optional) target registration.

    Returns:
        {"dns_name": str, "target_group_arn": str, "nlb_arn": str, "listener_arn": str}
    """
    tg_arn = create_target_group(
        client,
        name=tg_name or f"{nlb_name}-tg",
        vpc_id=vpc_id,
        port=target_port,
        health_check_path=health_check_path,
    )
    nlb_arn = create_nlb(client, nlb_name, subnet_ids, scheme=scheme)
    listener_arn = create_listener(
        client,
        load_balancer_arn=nlb_arn,
        target_group_arn=tg_arn,
        port=listener_port,
    )
    register_targets(client, tg_arn, instance_ids or [])

    # Fetch the DNS name from the live describe call so the caller can
    # see exactly what clients will hit.
    described = client.describe_load_balancers(LoadBalancerArns=[nlb_arn])
    dns_name = described["LoadBalancers"][0]["DNSName"]

    return {
        "dns_name": dns_name,
        "target_group_arn": tg_arn,
        "nlb_arn": nlb_arn,
        "listener_arn": listener_arn,
    }


# ── main ───────────────────────────────────────────────────────────────
def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a Network Load Balancer + target group + listener.",
    )
    parser.add_argument("--nlb-name", default=os.environ.get("NLB_NAME", "demo-nlb"))
    parser.add_argument("--vpc-id", default=os.environ.get("VPC_ID", "vpc-0123456789abcdef0"))
    parser.add_argument(
        "--subnet-ids",
        nargs="+",
        default=os.environ.get("SUBNET_IDS", "subnet-aaa subnet-bbb").split(),
    )
    parser.add_argument(
        "--tg-name",
        default=os.environ.get("TG_NAME"),
        help="Defaults to <nlb-name>-tg.",
    )
    parser.add_argument("--target-port", type=int, default=80)
    parser.add_argument("--listener-port", type=int, default=80)
    parser.add_argument(
        "--scheme",
        default=os.environ.get("NLB_SCHEME", "internet-facing"),
        choices=["internet-facing", "internal"],
    )
    parser.add_argument(
        "--instance-ids",
        nargs="*",
        default=[],
        help="Optional EC2 instance IDs to register. Empty = skip.",
    )
    args = parser.parse_args(argv)

    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("elbv2", region_name=region)

    result = create_nlb_with_target_group(
        client,
        nlb_name=args.nlb_name,
        vpc_id=args.vpc_id,
        subnet_ids=args.subnet_ids,
        tg_name=args.tg_name,
        target_port=args.target_port,
        listener_port=args.listener_port,
        scheme=args.scheme,
        instance_ids=args.instance_ids,
    )

    print()
    print("=" * 64)
    print(f"NLB DNS NAME       : {result['dns_name']}")
    print(f"TARGET GROUP ARN   : {result['target_group_arn']}")
    print(f"NLB ARN            : {result['nlb_arn']}")
    print(f"LISTENER ARN       : {result['listener_arn']}")
    print("=" * 64)
    print()
    print("Next step: point a CNAME (or A record using the static IPs)")
    print(f"for your domain at {result['dns_name']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
