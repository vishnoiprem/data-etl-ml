# Outputs — everything CI needs to deploy and smoke-test the service.
#
# Rule: outputs are the ONLY supported channel between Terraform and your
# pipeline. Scripts should read `terraform output -json`, never hardcode a
# service URL, because the URL changes when a region or name changes.

output "ecr_repository_url" {
  description = "Push your Docker image here."
  value       = aws_ecr_repository.app.repository_url
}

output "app_runner_service_url" {
  description = "Base URL of the deployed service."
  value       = aws_apprunner_service.app.service_url
}

output "healthz_url" {
  description = "Health check URL — use this for the post-deploy smoke test."
  value       = "${aws_apprunner_service.app.service_url}healthz"
}

output "log_group_name" {
  description = "CloudWatch log group for this service."
  value       = aws_cloudwatch_log_group.app.name
}

output "deployment_summary" {
  description = "Human-readable summary for CI logs."
  value = {
    environment = var.environment
    region      = var.aws_region
    account     = data.aws_caller_identity.current.account_id
    cpu         = var.cpu
    memory_mb   = var.memory
    min         = var.min_instances
    max         = var.max_instances
  }
}