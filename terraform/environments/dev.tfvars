# Development environment variables for AI News Agent

# Environment Configuration
environment = "dev"
aws_region  = "us-east-1"

# Lambda Configuration
lambda_memory_size           = 512
lambda_timeout              = 300
lambda_concurrent_executions = 5

# Application Configuration
search_query      = "Generative AI"
time_range_hours  = 72
max_articles      = 25
summary_length    = "medium"
model_name        = "amazon.nova-lite-v1:0"  # Use lite model for dev to save costs
model_provider    = "bedrock"

# SNS Configuration
email_endpoints = [
  "rob.w.walker@gmail.com"  # Only one email for dev testing
]

# EventBridge Configuration
schedule_expression = "rate(2 hours)"  # More frequent for dev testing

# Monitoring Configuration
error_threshold     = 3
duration_threshold  = 180000  # 3 minutes

# Logging Configuration
log_retention_days = 7   # Shorter retention for dev
log_level         = "DEBUG"

# Cost Monitoring Configuration
monthly_budget_limit     = "25.00"  # Lower budget for dev
lambda_budget_limit      = "10.00"
bedrock_budget_limit     = "10.00"  # Lower since using lite model
daily_cost_threshold     = 2.00     # Lower threshold for dev
cost_anomaly_threshold   = 5.00
enable_cost_dashboard    = true