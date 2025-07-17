# Backend configuration for development environment
# Usage: terraform init -backend-config=backend-dev.hcl

bucket         = "ai-news-agent-terraform-state-dev"
key            = "ai-news-agent/dev/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "ai-news-agent-terraform-lock-dev"

# Optional: Enable versioning and lifecycle policies on the S3 bucket
# versioning = true