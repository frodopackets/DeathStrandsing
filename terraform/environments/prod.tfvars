# Production environment variables for AI News Agent

# Environment Configuration
environment = "prod"
aws_region  = "us-east-1"

# Lambda Configuration
lambda_memory_size           = 1024  # More memory for production
lambda_timeout              = 300
lambda_concurrent_executions = 10

# Application Configuration
search_query      = "Generative AI"
time_range_hours  = 72
max_articles      = 50
summary_length    = "medium"
model_name        = "amazon.nova-pro-v1:0"  # Use pro model for production quality
model_provider    = "bedrock"

# SNS Configuration
email_endpoints = [
  "rob.w.walker@gmail.com",
  "robert.walker2@regions.com"
]

# EventBridge Configuration
schedule_expression = "rate(1 day)"  # Daily execution for production

# Monitoring Configuration
error_threshold     = 5
duration_threshold  = 240000  # 4 minutes

# Logging Configuration
log_retention_days = 30  # Standard retention for production
log_level         = "INFO"

# Cost Monitoring Configuration
monthly_budget_limit     = "100.00"  # Higher budget for production
lambda_budget_limit      = "40.00"
bedrock_budget_limit     = "50.00"   # Higher since using pro model
daily_cost_threshold     = 10.00     # Higher threshold for production
cost_anomaly_threshold   = 20.00
enable_cost_dashboard    = true