# Main Terraform configuration for AI News Agent
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for state management
  backend "s3" {
    # These values will be provided via backend config file or CLI
    # bucket         = "your-terraform-state-bucket"
    # key            = "ai-news-agent/terraform.tfstate"
    # region         = "us-east-1"
    # encrypt        = true
    # dynamodb_table = "terraform-state-lock"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "AI News Agent"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# KMS key for encryption
resource "aws_kms_key" "ai_news_agent" {
  description             = "KMS key for AI News Agent encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-kms-key"
  }
}

# KMS key alias
resource "aws_kms_alias" "ai_news_agent" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.ai_news_agent.key_id
}

# SNS Topic Module
module "sns" {
  source = "./modules/sns"

  topic_name    = "${var.project_name}-${var.environment}-notifications"
  kms_key_arn   = aws_kms_key.ai_news_agent.arn
  email_endpoints = var.email_endpoints

  tags = {
    Name = "${var.project_name}-${var.environment}-sns"
  }
}

# Lambda Function Module
module "lambda" {
  source = "./modules/lambda"

  function_name    = "${var.project_name}-${var.environment}"
  runtime          = "python3.11"
  handler          = "lambda_function.lambda_handler"
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  sns_topic_arn    = module.sns.sns_topic_arn
  kms_key_arn      = aws_kms_key.ai_news_agent.arn
  log_retention_days = var.log_retention_days

  environment_variables = {
    SEARCH_QUERY        = var.search_query
    TIME_RANGE_HOURS    = tostring(var.time_range_hours)
    SNS_TOPIC_ARN       = module.sns.sns_topic_arn
    MAX_ARTICLES        = tostring(var.max_articles)
    SUMMARY_LENGTH      = var.summary_length
    MODEL_NAME          = var.model_name
    MODEL_PROVIDER      = var.model_provider
    ENVIRONMENT         = var.environment
    LOG_LEVEL          = var.log_level
  }

  reserved_concurrent_executions = var.lambda_concurrent_executions

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda"
  }
}

# EventBridge Scheduler Module
module "eventbridge" {
  source = "./modules/eventbridge"

  rule_name         = "${var.project_name}-${var.environment}-schedule"
  schedule_expression = var.schedule_expression
  lambda_function_arn = module.lambda.lambda_function_arn
  lambda_function_name = module.lambda.lambda_function_name

  tags = {
    Name = "${var.project_name}-${var.environment}-eventbridge"
  }
}

# CloudWatch Monitoring Module
module "cloudwatch" {
  source = "./modules/cloudwatch"

  application_name           = "${var.project_name}-${var.environment}"
  lambda_function_name       = module.lambda.lambda_function_name
  sns_topic_name            = module.sns.sns_topic_name
  kms_key_arn               = aws_kms_key.ai_news_agent.arn
  
  # Log group configuration
  application_log_group_name = "/aws/lambda/${var.project_name}-${var.environment}"
  error_log_group_name      = "/aws/lambda/${var.project_name}-${var.environment}/errors"
  audit_log_group_name      = "/aws/lambda/${var.project_name}-${var.environment}/audit"
  log_retention_days        = var.log_retention_days
  error_log_retention_days  = var.log_retention_days * 3  # Keep errors longer
  audit_log_retention_days  = 365  # CIS compliance requirement
  
  # Custom metrics configuration
  custom_metrics_namespace = "AiNewsAgent/${var.environment}"
  error_pattern           = "[ERROR]"
  success_pattern         = "[SUCCESS]"
  articles_processed_pattern = "[ARTICLES_PROCESSED]"
  
  # Alarm thresholds
  error_alarm_threshold     = var.error_threshold
  duration_alarm_threshold  = var.duration_threshold
  
  # Alarm actions - use SNS topic for notifications
  alarm_actions = [module.sns.sns_topic_arn]
  ok_actions    = [module.sns.sns_topic_arn]
  composite_alarm_actions = [module.sns.sns_topic_arn]
  composite_ok_actions    = [module.sns.sns_topic_arn]

  tags = {
    Name = "${var.project_name}-${var.environment}-monitoring"
  }
}

# Cost Monitoring Module
module "cost_monitoring" {
  source = "./modules/cost-monitoring"

  application_name      = "${var.project_name}-${var.environment}"
  lambda_function_name  = module.lambda.lambda_function_name
  
  # Budget configuration
  monthly_budget_limit  = var.monthly_budget_limit
  lambda_budget_limit   = var.lambda_budget_limit
  bedrock_budget_limit  = var.bedrock_budget_limit
  budget_alert_emails   = var.email_endpoints
  
  # Cost alarm configuration
  daily_cost_threshold  = var.daily_cost_threshold
  cost_alarm_actions    = [module.sns.sns_topic_arn]
  
  # Cost anomaly detection
  cost_anomaly_email    = var.email_endpoints[0]  # Use first email for anomaly alerts
  anomaly_threshold     = var.cost_anomaly_threshold
  
  # Dashboard configuration
  enable_cost_dashboard = var.enable_cost_dashboard

  tags = {
    Name = "${var.project_name}-${var.environment}-cost-monitoring"
  }
}