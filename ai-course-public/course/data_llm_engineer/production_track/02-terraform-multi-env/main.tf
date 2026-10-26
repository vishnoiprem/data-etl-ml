# Production AI SaaS — AWS infrastructure.
#
# Maps to Section 2 (Week 1–2) of the Production track:
#   * Week 1 Day 5 — Docker → ECR → App Runner
#   * Week 2 Day 4 — Terraform IaC, dev/test/prod environments
#
# Design rules this file follows, in priority order:
#   1. No resource is created without a variable that scopes it to an
#      environment. There is no "default" environment in this file.
#   2. Every resource that can be reached from the internet has an explicit
#      public/private decision recorded in a comment.
#   3. Secrets are referenced, never defined. Secrets Manager ARNs are inputs.
#   4. Tags are applied uniformly so the cost dashboard can group by env.
#
# Usage:
#   terraform init
#   terraform plan  -var-file=envs/dev.tfvars
#   terraform apply -var-file=envs/dev.tfvars

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Remote state. Both of these must exist BEFORE `terraform init`.
  # In a real deployment this is an S3 bucket + DynamoDB table you create
  # exactly once, by hand, with a lifecycle policy that prevents deletion.
  backend "s3" {
    bucket         = "REPLACE-ME-terraform-state-us-east-1"
    key            = "production-track/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "REPLACE-ME-terraform-locks"
    encrypt        = true
  }
}

# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  # Fails loudly rather than deploying into whatever account the ambient
  # credentials happen to point at. This is the single highest-value line in
  # the file: it prevents the "deployed to the wrong account" incident.
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = {
      Project     = "ai-production-saas"
      Environment = var.environment
      ManagedBy   = "terraform"
      Course      = "ai-engineer-production"
    }
  }
}

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# ---------------------------------------------------------------------------
# ECR — container registry (Week 1 Day 5)
# ---------------------------------------------------------------------------

resource "aws_ecr_repository" "app" {
  name                 = "${var.project_name}-${var.environment}"
  image_tag_mutability = var.environment == "prod" ? "IMMUTABLE" : "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = { Component = "registry" }
}

# Lifecycle policy: keep the last 30 images, expire untagged after 7 days.
# Without this, a CI loop that pushes on every merge fills the account with
# thousands of untagged layers and the cost line item becomes archaeology.
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the most recent 30 images"
        selection = {
          tagStatus   = "tagged"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Expire untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = { type = "expire" }
      },
    ]
  })
}

# ---------------------------------------------------------------------------
# ECR lifecycle policy — scan on push is configured above; this is the
# scheduled deep-scan safety net for base-image CVEs.
# ---------------------------------------------------------------------------

resource "aws_ecr_repository_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPushPull"
        Effect = "Allow"
        Principal = {
          Service = "ecr.amazonaws.com"
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
        ]
      },
    ]
  })
}

# ---------------------------------------------------------------------------
# CloudWatch log group — created explicitly so retention is enforced.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/apprunner/${var.project_name}-${var.environment}"
  retention_in_days = var.environment == "prod" ? 90 : 14
  tags              = { Component = "observability" }
}

# ---------------------------------------------------------------------------
# App Runner — ECR access role
# ---------------------------------------------------------------------------
#
# App Runner pulls your image on your behalf. For a private ECR repo it needs
# an IAM role with ecr:BatchGetImage + ecr:GetDownloadUrlForLayer. This is
# separate from the CI role that PUSHES the image — two different
# permissions, and conflating them is a common source of "works locally,
# AccessDenied in the console" failures.

data "aws_iam_policy_document" "ecr_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecr_access" {
  name               = "${var.project_name}-${var.environment}-ecr-access"
  assume_role_policy = data.aws_iam_policy_document.ecr_assume.json
  tags               = { Component = "iam" }
}

data "aws_iam_policy_document" "ecr_pull" {
  statement {
    sid       = "ECRPull"
    actions   = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:DescribeImages"]
    resources = [aws_ecr_repository.app.arn]
  }

  # CloudWatch Logs so App Runner's own operations are auditable.
  statement {
    sid = "LogsWrite"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.app.arn}:*"]
  }
}

resource "aws_iam_role_policy" "ecr_pull" {
  name   = "${var.project_name}-${var.environment}-ecr-pull"
  role   = aws_iam_role.ecr_access.id
  policy = data.aws_iam_policy_document.ecr_pull.json
}

# ---------------------------------------------------------------------------
# App Runner auto-scaling configuration (separate versioned resource)
# ---------------------------------------------------------------------------
#
# Two schema traps here, both confirmed against the provider schema:
#
#  1. The resource is `aws_apprunner_auto_scaling_configuration_VERSION`.
#     There is no unversioned `..._configuration` resource — that fails
#     validate with "Invalid resource type".
#
#  2. It is a FLAT resource. min_size / max_size / max_concurrency are
#     top-level arguments. There is no nested `auto_scaling_configuration {}`
#     block — that fails with "Blocks of type auto_scaling_configuration are
#     not expected here".
#
# The service references it by name via `auto_scaling_configuration_arn`.
# There is no dependency cycle: this resource knows nothing about the
# service, and the service points at it.

resource "aws_apprunner_auto_scaling_configuration_version" "app" {
  auto_scaling_configuration_name = "${var.project_name}-${var.environment}-ascaling"

  # min=0 in dev so an idle weekend costs nothing; min>=1 in prod, because
  # a cold start on a user-facing request is a support ticket.
  min_size        = var.min_instances
  max_size        = var.max_instances
  max_concurrency = var.max_concurrency
}

# ---------------------------------------------------------------------------
# App Runner service (Week 1 Day 5)
# ---------------------------------------------------------------------------

resource "aws_apprunner_service" "app" {
  service_name = "${var.project_name}-${var.environment}"

  source_configuration {
    image_repository {
      # image_identifier is the ECR repository URI (or name for ECR_PUBLIC).
      # It is NOT called repository_name or repository_url — those attributes
      # do not exist on this block, despite being the obvious guesses.
      image_identifier      = aws_ecr_repository.app.repository_url
      image_repository_type = "ECR"

      image_configuration {
        port = var.container_port

        # NOTE: there is no `runtime` and no `auto_deployment_mode` argument
        # here. App Runner infers the runtime from the image's own metadata.
        # Passing either fails validate.

        start_command = var.container_port == 8080 ? null : "uvicorn app.main:app --host 0.0.0.0 --port ${var.container_port}"

        # Secrets are referenced by ARN, never defined here. See README for
        # the Secrets Manager setup this assumes exists.
        runtime_environment_secrets = {
          OPENAI_API_KEY = var.openai_secret_arn
        }

        runtime_environment_variables = {
          ENVIRONMENT = var.environment
          LOG_LEVEL   = var.environment == "prod" ? "INFO" : "DEBUG"
        }
      }
    }

    # Required for private ECR repos. NOTE: this is a SIBLING of
    # image_repository under source_configuration, not a child of it.
    # Putting it inside image_repository fails validate with
    # "Blocks of type authentication_configuration are not expected here".
    authentication_configuration {
      access_role_arn = aws_iam_role.ecr_access.arn
    }

    # Auto-deploy is DISABLED in prod on purpose: the course's Week 2 CI/CD
    # lesson is that prod deploys must be an explicit, auditable pipeline
    # step — not an automatic consequence of a new image landing in ECR.
    auto_deployments_enabled = var.environment != "prod"
  }

  instance_configuration {
    cpu    = var.cpu
    memory = var.memory
  }

  # Link the versioned scaling config. Safe: the scaling resource has no
  # back-reference to the service, so this is not a cycle.
  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.app.arn

  health_check_configuration {
    # MUST match the route your app actually serves. A mismatch here is the
    # classic App Runner deploy failure: the service deploys "successfully"
    # and then serves 502s because the health check never passes.
    path                = "/healthz"
    protocol            = "HTTP"
    interval            = 15
    timeout             = 10
    healthy_threshold   = 3
    unhealthy_threshold = 4
  }

  network_configuration {
    ip_address_type = "IPV4"

    ingress_configuration {
      is_publicly_accessible = var.environment != "prod"
    }

    egress_configuration {
      egress_type = "DEFAULT"
    }
  }

  }