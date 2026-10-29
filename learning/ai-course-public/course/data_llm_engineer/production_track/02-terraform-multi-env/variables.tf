# Variables for the production AI SaaS infrastructure.
#
# Every variable here has NO default for the environment/account scoping —
# that is deliberate. A default environment is how infrastructure ends up in
# the wrong account, and `allowed_account_ids` in main.tf is the backstop.

# ---------------------------------------------------------------------------
# Environment scoping (no defaults — force the operator to choose)
# ---------------------------------------------------------------------------

variable "environment" {
  description = "Deployment environment. Gates log retention, auto-deploy, and min instances."
  type        = string

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be one of: dev, test, prod."
  }
}

variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = <<-EOT
    The 12-digit AWS account ID this stack is allowed to deploy into.
    Wired into provider "allowed_account_ids" so a mis-authenticated CLI
    fails at plan time instead of creating resources in the wrong account.
  EOT
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "aws_account_id must be a 12-digit AWS account ID."
  }
}

variable "project_name" {
  description = "Short project slug. Prefixed to every resource name."
  type        = string
  default     = "ai-saas"
}

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

variable "container_port" {
  description = <<-EOT
    Port the container listens on. MUST match the uvicorn --port in your
    Dockerfile AND the health check path in main.tf. A mismatch here is the
    single most common App Runner deploy failure.
  EOT
  type        = number
  default     = 8080

  validation {
    condition     = var.container_port >= 1 && var.container_port <= 65535
    error_message = "container_port must be a valid TCP port."
  }
}

# ---------------------------------------------------------------------------
# Sizing
# ---------------------------------------------------------------------------

variable "cpu" {
  description = "App Runner CPU. Valid: 256, 512, 1024, 2048, 4096, vCPU:0.5, vCPU:1, vCPU:2, vCPU:4."
  type        = number
  default     = 1024

  validation {
    condition = contains(
      [256, 512, 1024, 2048, 4096],
      var.cpu
    )
    error_message = "cpu must be one of 256, 512, 1024, 2048, 4096."
  }
}

variable "memory" {
  description = "App Runner memory in MB. Valid: 512, 1024, 2048, 3072, 4096, 6144, 8192, 10240, 12288."
  type        = number
  default     = 2048

  validation {
    condition = contains(
      [512, 1024, 2048, 3072, 4096, 6144, 8192, 10240, 12288],
      var.memory
    )
    error_message = "memory must be a valid App Runner memory size in MB."
  }
}

variable "min_instances" {
  description = <<-EOT
    Minimum warm instances. 0 in dev (scale to zero, pay nothing when idle).
    >= 1 in prod — a cold start on a user-facing request is a support ticket.
  EOT
  type        = number
  default     = 0

  validation {
    condition     = var.min_instances >= 0
    error_message = "min_instances must be >= 0."
  }
}

variable "max_instances" {
  description = "Maximum instances under load. Set a real ceiling; unbounded scaling is how a traffic spike becomes a four-figure AWS bill."
  type        = number
  default     = 4

  validation {
    condition     = var.max_instances >= var.min_instances
    error_message = "max_instances must be >= min_instances."
  }
}

variable "max_concurrency" {
  description = "Requests per instance before scaling out. Lower = smoother, higher = cheaper."
  type        = number
  default     = 50
}

# ---------------------------------------------------------------------------
# Secrets (referenced, never defined)
# ---------------------------------------------------------------------------

variable "openai_secret_arn" {
  description = <<-EOT
    ARN of the Secrets Manager secret holding OPENAI_API_KEY.

    This stack REFERENCES the secret; it does not create it. Create the
    secret out of band first:

      aws secretsmanager create-secret --name prod/openai \
        --secret-string "{\"OPENAI_API_KEY\":\"sk-...\"}"

    Why out of band: a secret created by the same Terraform run that consumes
    it lands in the state file in plaintext, which defeats the purpose of
    using Secrets Manager at all.
  EOT
  type        = string

  validation {
    condition     = can(regex("^arn:aws(-[a-z]+)?:secretsmanager:", var.openai_secret_arn))
    error_message = "openai_secret_arn must be a Secrets Manager ARN."
  }
}