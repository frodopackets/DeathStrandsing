# Outputs for CloudWatch monitoring module

# Log Groups
output "application_log_group_name" {
  description = "Name of the application log group"
  value       = aws_cloudwatch_log_group.application_logs.name
}

output "application_log_group_arn" {
  description = "ARN of the application log group"
  value       = aws_cloudwatch_log_group.application_logs.arn
}

output "error_log_group_name" {
  description = "Name of the error log group"
  value       = aws_cloudwatch_log_group.error_logs.name
}

output "error_log_group_arn" {
  description = "ARN of the error log group"
  value       = aws_cloudwatch_log_group.error_logs.arn
}

output "audit_log_group_name" {
  description = "Name of the audit log group"
  value       = aws_cloudwatch_log_group.audit_logs.name
}

output "audit_log_group_arn" {
  description = "ARN of the audit log group"
  value       = aws_cloudwatch_log_group.audit_logs.arn
}

# Metric Filters
output "error_metric_filter_name" {
  description = "Name of the error metric filter"
  value       = aws_cloudwatch_log_metric_filter.error_metric_filter.name
}

output "success_metric_filter_name" {
  description = "Name of the success metric filter"
  value       = aws_cloudwatch_log_metric_filter.success_metric_filter.name
}

output "articles_processed_filter_name" {
  description = "Name of the articles processed metric filter"
  value       = aws_cloudwatch_log_metric_filter.articles_processed_filter.name
}

# Alarms
output "lambda_error_alarm_name" {
  description = "Name of the Lambda error alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_error_alarm.alarm_name
}

output "lambda_error_alarm_arn" {
  description = "ARN of the Lambda error alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_error_alarm.arn
}

output "lambda_duration_alarm_name" {
  description = "Name of the Lambda duration alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_duration_alarm.alarm_name
}

output "lambda_duration_alarm_arn" {
  description = "ARN of the Lambda duration alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_duration_alarm.arn
}

output "lambda_throttle_alarm_name" {
  description = "Name of the Lambda throttle alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_throttle_alarm.alarm_name
}

output "lambda_throttle_alarm_arn" {
  description = "ARN of the Lambda throttle alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_throttle_alarm.arn
}

output "custom_error_alarm_name" {
  description = "Name of the custom error alarm"
  value       = aws_cloudwatch_metric_alarm.custom_error_alarm.alarm_name
}

output "custom_error_alarm_arn" {
  description = "ARN of the custom error alarm"
  value       = aws_cloudwatch_metric_alarm.custom_error_alarm.arn
}

output "sns_failure_alarm_name" {
  description = "Name of the SNS failure alarm (if created)"
  value       = var.sns_topic_name != null ? aws_cloudwatch_metric_alarm.sns_failure_alarm[0].alarm_name : null
}

output "sns_failure_alarm_arn" {
  description = "ARN of the SNS failure alarm (if created)"
  value       = var.sns_topic_name != null ? aws_cloudwatch_metric_alarm.sns_failure_alarm[0].arn : null
}

output "system_health_alarm_name" {
  description = "Name of the composite system health alarm"
  value       = aws_cloudwatch_composite_alarm.system_health_alarm.alarm_name
}

output "system_health_alarm_arn" {
  description = "ARN of the composite system health alarm"
  value       = aws_cloudwatch_composite_alarm.system_health_alarm.arn
}

# Dashboard
output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.ai_news_dashboard.dashboard_name
}

output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.ai_news_dashboard.dashboard_name}"
}

# Custom Metrics Namespace
output "custom_metrics_namespace" {
  description = "Namespace for custom CloudWatch metrics"
  value       = var.custom_metrics_namespace
}

# All alarm ARNs for easy reference
output "all_alarm_arns" {
  description = "List of all CloudWatch alarm ARNs"
  value = compact([
    aws_cloudwatch_metric_alarm.lambda_error_alarm.arn,
    aws_cloudwatch_metric_alarm.lambda_duration_alarm.arn,
    aws_cloudwatch_metric_alarm.lambda_throttle_alarm.arn,
    aws_cloudwatch_metric_alarm.custom_error_alarm.arn,
    var.sns_topic_name != null ? aws_cloudwatch_metric_alarm.sns_failure_alarm[0].arn : null,
    aws_cloudwatch_composite_alarm.system_health_alarm.arn
  ])
}