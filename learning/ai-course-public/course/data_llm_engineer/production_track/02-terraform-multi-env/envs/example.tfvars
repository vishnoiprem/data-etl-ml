# Example variable file — COPY to envs/dev.tfvars and edit.
#
# Never commit a populated .tfvars for prod. Use environment variables
# (TF_VAR_*) from your CI secret store instead.

environment     = "dev"
aws_region     = "us-east-1"
aws_account_id = "123456789012"   # your 12-digit account ID
project_name   = "ai-saas"

container_port = 8080

# Dev: scale to zero, small instances, high concurrency (cheap).
cpu              = 512
memory           = 1024
min_instances    = 0
max_instances    = 2
max_concurrency  = 100

# Secrets Manager ARN holding OPENAI_API_KEY. Create the secret out of band.
openai_secret_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:dev/openai-AbCdEf"
