"""test_gwlb_create.py — pytest suite for gwlb_create.py.

> Author: Prem Vishnoi <prem.vishnoi@example.com>
> Section: 08 — Gateway Load Balancer + Course Wrap-up
> Lecture: L37 — GWLB Hands-On

The tests use ``moto.mock_aws`` to stand up an in-memory AWS account,
provision a real VPC and two subnets, then call
:func:`gwlb_create.create_gwlb` and assert on the returned ARNs.

Three tests:

* ``test_gwlb_type_is_gateway`` — the load balancer Type is ``gateway``.
* ``test_target_group_protocol_geneve`` — the target group uses the
  GENEVE protocol on UDP port 6081.
* ``test_listener_forwards_to_target_group`` — the listener exists,
  defaults to a forward action, and points at the target group.
"""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from gwlb_create import create_gwlb


# ── Test fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def aws_env():
    """Provision a VPC + two subnets in two AZs, then build a GWLB on top."""
    with mock_aws():
        region = "us-east-1"
        ec2 = boto3.client("ec2", region_name=region)
        azs = ec2.describe_availability_zones()["AvailabilityZones"]
        az_a = azs[0]["ZoneName"]
        az_b = azs[1]["ZoneName"]

        vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
        subnet_a = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az_a
        )["Subnet"]["SubnetId"]
        subnet_b = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone=az_b
        )["Subnet"]["SubnetId"]

        elbv2 = boto3.client("elbv2", region_name=region)
        result = create_gwlb(
            name="demo-gwlb",
            subnet_ids=[subnet_a, subnet_b],
            vpc_id=vpc_id,
            region_name=region,
            client=elbv2,
        )
        yield {
            "region": region,
            "vpc_id": vpc_id,
            "subnet_a": subnet_a,
            "subnet_b": subnet_b,
            "result": result,
            "elbv2": elbv2,
        }


# ── Tests ──────────────────────────────────────────────────────────────


def test_gwlb_type_is_gateway(aws_env):
    """The load balancer must be of type 'gateway'."""
    elbv2 = aws_env["elbv2"]
    lb_arn = aws_env["result"].load_balancer_arn

    response = elbv2.describe_load_balancers(LoadBalancerArns=[lb_arn])
    lbs = response["LoadBalancers"]
    assert len(lbs) == 1
    assert lbs[0]["Type"] == "gateway"
    # And it must be deployed in exactly the two subnets we passed in.
    # boto3 returns AvailabilityZones as a list of {SubnetId, ZoneName}
    # dicts for a network/gateway load balancer.
    az_subnets = [az["SubnetId"] for az in lbs[0]["AvailabilityZones"]]
    assert sorted(az_subnets) == sorted(
        [aws_env["subnet_a"], aws_env["subnet_b"]]
    )


def test_target_group_protocol_geneve(aws_env):
    """The target group must be GENEVE on UDP 6081 with HTTP health checks on /health."""
    elbv2 = aws_env["elbv2"]
    tg_arn = aws_env["result"].target_group_arn

    response = elbv2.describe_target_groups(TargetGroupArns=[tg_arn])
    tgs = response["TargetGroups"]
    assert len(tgs) == 1
    tg = tgs[0]
    assert tg["Protocol"] == "GENEVE"
    assert tg["Port"] == 6081
    assert tg["HealthCheckProtocol"] == "HTTP"
    assert tg["HealthCheckPath"] == "/health"
    assert tg["VpcId"] == aws_env["vpc_id"]


def test_listener_forwards_to_target_group(aws_env):
    """The listener must exist, default to a forward action, and target the TG."""
    elbv2 = aws_env["elbv2"]
    lb_arn = aws_env["result"].load_balancer_arn
    tg_arn = aws_env["result"].target_group_arn

    response = elbv2.describe_listeners(LoadBalancerArn=lb_arn)
    listeners = response["Listeners"]
    assert len(listeners) == 1
    listener = listeners[0]

    # Real AWS pins GWLB listeners to GENEVE/6081. moto returns an
    # empty Protocol string (it rejects the explicit Protocol/Port
    # params). We accept either to be robust against both backends.
    assert listener["Protocol"] in ("", "GENEVE")

    # Default action must be a forward to the target group.
    actions = listener["DefaultActions"]
    assert len(actions) == 1
    assert actions[0]["Type"] == "forward"
    assert actions[0]["TargetGroupArn"] == tg_arn
