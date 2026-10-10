# launch_instance.py

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03 (Creating an EC2 Instance)
> **Demo for:** L18 — Section Recap

A small boto3 script that launches **one** EC2 instance, tags it
identifiably, and waits for the instance to enter the `running`
state. It is the canonical end-to-end demo for section 3.

## What the script does

1. Parses CLI arguments for the AMI id, instance type, key name,
   security group ids, subnet id, optional user-data file, and a
   name tag.
2. Calls `ec2.run_instances()` with a `TagSpecifications` block that
   sets `Name`, `CreatedBy=aws_ec2_course`, and `CourseSection=3`.
3. Calls `ec2.get_waiter("instance_running").wait(...)` so the script
   blocks until the instance is actually reachable (or until the
   waiter times out).
4. Prints the instance id and (best-effort) the public DNS name.

## Files

| File | Purpose |
|---|---|
| `launch_instance.py` | The script itself. |
| `test_launch_instance.py` | 6 `moto`-based pytest tests. |

## IAM policy required (real AWS)

The principal running this script needs permission to launch an
instance, describe it, and pass an IAM role / user data through. The
shortest reasonable policy is below. **Scope it to your own prefix
and region before applying it to a real account.**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowRunInstances",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:DescribeInstances",
        "ec2:CreateTags",
        "ec2:DescribeImages",
        "ec2:DescribeKeyPairs",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets"
      ],
      "Resource": "*"
    }
  ]
}
```

For production you should also grant `iam:PassRole` (so an instance
profile can be attached) and explicitly tag the resources that should
receive the `Name` tag.

## CLI reference

```
python launch_instance.py \
  --ami-id ami-0abcdef1234567890 \
  --instance-type t3.micro \
  --key-name my-key \
  --security-group-ids sg-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0 \
  --user-data-file ./bootstrap.sh \
  --name demo-instance
```

| Flag | Required | Default | Notes |
|---|---|---|---|
| `--ami-id` | yes | – | An AMI id in the target region. |
| `--instance-type` | no | `t3.micro` | Any EC2 instance type. |
| `--key-name` | yes | – | Must already exist in the target region. |
| `--security-group-ids` | yes | – | One or more `sg-…` ids. |
| `--subnet-id` | yes | – | Subnet in the target VPC. |
| `--user-data-file` | no | – | Path to a bash / cloud-init script. |
| `--name` | no | `ec2-course-instance` | Value for the `Name` tag. |
| `--region` | no | `AWS_REGION` env or `us-east-1` | AWS region. |

The region is read from the `AWS_REGION` environment variable, or
`us-east-1` if that is unset. Override with `--region` for a
one-off run.

## Running against moto (offline, no AWS)

```bash
cd 03_creating_ec2/code/launch_instance
python -m pytest -v
```

Expected: **6 passed** in under 5 seconds. No AWS calls leave your
machine.

## Running against real AWS

1. Install dependencies (one time, from the repo root):

   ```bash
   pip install -r requirements.txt
   ```

2. Configure credentials (one time):

   ```bash
   aws configure sso   # or: aws configure
   ```

3. Find a recent Amazon Linux 2 AMI in your region:

   ```bash
   aws ec2 describe-images \
     --owners amazon \
     --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
     --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" \
     --output text
   ```

4. Create a key pair and security group (if you don't have one):

   ```bash
   aws ec2 create-key-pair --key-name my-course-key \
     --query "KeyMaterial" --output text > my-course-key.pem
   chmod 400 my-course-key.pem

   aws ec2 create-security-group \
     --group-name course-sg \
     --description "course security group" \
     --vpc-id vpc-0123456789abcdef0
   aws ec2 authorize-security-group-ingress \
     --group-id sg-0123456789abcdef0 \
     --protocol tcp --port 22 --cidr 0.0.0.0/0
   ```

5. Run the script:

   ```bash
   python launch_instance.py \
     --ami-id ami-0123456789abcdef0 \
     --key-name my-course-key \
     --security-group-ids sg-0123456789abcdef0 \
     --subnet-id subnet-0123456789abcdef0 \
     --name demo-instance
   ```

6. Clean up so you don't get billed:

   ```bash
   aws ec2 terminate-instances --instance-ids i-0123456789abcdef0
   ```

## Why a waiter?

`run_instances()` returns the moment AWS has **accepted** the request,
not when the instance is reachable. If you immediately try to SSH in
or `describe_instances` for a public IP, you'll race the hypervisor.
The `instance_running` waiter polls `describe_instances()` every
~15 seconds (with exponential backoff up to 40s) until `State.Name`
transitions to `running`, then returns. That's why `launch_instance()`
uses the waiter rather than just sleeping for a fixed amount of time.

## Why pass `MinCount=1, MaxCount=1`?

The boto3 default is `MinCount=1, MaxCount=1`, but we set them
explicitly to make the **single instance** intent obvious. Spot
fleets and multi-instance launches deliberately use higher values;
for this script we want exactly one.
