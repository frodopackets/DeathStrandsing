# Backend configuration for production environment
# Usage: terraform init -backend-config=backend-prod.hcl

bucket         = "ai-news-agent-terraform-state-prod"
key            = "ai-news-agent/prod/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "ai-news-agent-terraform-lock-prod"

# Optional: Enable versioning and lifecycle policies on the S3 bucket
# versioning = true