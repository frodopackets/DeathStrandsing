# Outputs for AI News Agent Terraform configuration

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.lambda_function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.lambda.lambda_function_arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic"
  value       = module.sns.sns_topic_arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic"
  value       = module.sns.sns_topic_name
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.lambda.lambda_log_group_name
}

output "kms_key_id" {
  description = "ID of the KMS key"
  value       = aws_kms_key.ai_news_agent.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = aws_kms_key.ai_news_agent.arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = module.eventbridge.eventbridge_rule_name
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

# Cost Monitoring Outputs
output "monthly_budget_name" {
  description = "Name of the monthly budget"
  value       = module.cost_monitoring.monthly_budget_name
}

output "cost_dashboard_name" {
  description = "Name of the cost monitoring dashboard"
  value       = module.cost_monitoring.cost_dashboard_name
}

output "cost_anomaly_detector_arn" {
  description = "ARN of the cost anomaly detector"
  value       = module.cost_monitoring.cost_anomaly_detector_arn
}