# CloudWatch monitoring Terraform module for AI News Agent

# CloudWatch log group for application logs
resource "aws_cloudwatch_log_group" "application_logs" {
  name              = var.application_log_group_name
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# CloudWatch log group for error logs
resource "aws_cloudwatch_log_group" "error_logs" {
  name              = var.error_log_group_name
  retention_in_days = var.error_log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# CloudWatch log group for audit logs (CIS compliance)
resource "aws_cloudwatch_log_group" "audit_logs" {
  name              = var.audit_log_group_name
  retention_in_days = var.audit_log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# Custom metric filter for error detection
resource "aws_cloudwatch_log_metric_filter" "error_metric_filter" {
  name           = "${var.application_name}-error-count"
  log_group_name = aws_cloudwatch_log_group.application_logs.name
  pattern        = var.error_pattern

  metric_transformation {
    name      = "ErrorCount"
    namespace = var.custom_metrics_namespace
    value     = "1"
    default_value = "0"
  }
}

# Custom metric filter for successful executions
resource "aws_cloudwatch_log_metric_filter" "success_metric_filter" {
  name           = "${var.application_name}-success-count"
  log_group_name = aws_cloudwatch_log_group.application_logs.name
  pattern        = var.success_pattern

  metric_transformation {
    name      = "SuccessCount"
    namespace = var.custom_metrics_namespace
    value     = "1"
    default_value = "0"
  }
}

# Custom metric filter for news articles processed
resource "aws_cloudwatch_log_metric_filter" "articles_processed_filter" {
  name           = "${var.application_name}-articles-processed"
  log_group_name = aws_cloudwatch_log_group.application_logs.name
  pattern        = var.articles_processed_pattern

  metric_transformation {
    name      = "ArticlesProcessed"
    namespace = var.custom_metrics_namespace
    value     = "$count"
    default_value = "0"
  }
}

# CloudWatch alarm for Lambda function errors
resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  alarm_name          = "${var.application_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.error_alarm_evaluation_periods
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.error_alarm_period
  statistic           = "Sum"
  threshold           = var.error_alarm_threshold
  alarm_description   = "This metric monitors Lambda function errors"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = var.tags
}

# CloudWatch alarm for Lambda function duration
resource "aws_cloudwatch_metric_alarm" "lambda_duration_alarm" {
  alarm_name          = "${var.application_name}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.duration_alarm_evaluation_periods
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = var.duration_alarm_period
  statistic           = "Average"
  threshold           = var.duration_alarm_threshold
  alarm_description   = "This metric monitors Lambda function duration"
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = var.tags
}

# CloudWatch alarm for Lambda function throttles
resource "aws_cloudwatch_metric_alarm" "lambda_throttle_alarm" {
  alarm_name          = "${var.application_name}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.throttle_alarm_evaluation_periods
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = var.throttle_alarm_period
  statistic           = "Sum"
  threshold           = var.throttle_alarm_threshold
  alarm_description   = "This metric monitors Lambda function throttles"
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = var.tags
}

# CloudWatch alarm for custom error metric
resource "aws_cloudwatch_metric_alarm" "custom_error_alarm" {
  alarm_name          = "${var.application_name}-custom-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.custom_error_alarm_evaluation_periods
  metric_name         = "ErrorCount"
  namespace           = var.custom_metrics_namespace
  period              = var.custom_error_alarm_period
  statistic           = "Sum"
  threshold           = var.custom_error_alarm_threshold
  alarm_description   = "This metric monitors application-specific errors"
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  tags = var.tags
}

# CloudWatch alarm for SNS message failures
resource "aws_cloudwatch_metric_alarm" "sns_failure_alarm" {
  count               = var.sns_topic_name != null ? 1 : 0
  alarm_name          = "${var.application_name}-sns-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.sns_failure_alarm_evaluation_periods
  metric_name         = "NumberOfMessagesFailed"
  namespace           = "AWS/SNS"
  period              = var.sns_failure_alarm_period
  statistic           = "Sum"
  threshold           = var.sns_failure_alarm_threshold
  alarm_description   = "This metric monitors SNS message delivery failures"
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    TopicName = var.sns_topic_name
  }

  tags = var.tags
}

# CloudWatch dashboard for monitoring
resource "aws_cloudwatch_dashboard" "ai_news_dashboard" {
  count = var.enable_dashboard ? 1 : 0
  dashboard_name = "${var.application_name}-dashboard"

  dashboard_body = templatefile("${path.module}/dashboard.json", {
    lambda_function_name    = var.lambda_function_name
    sns_topic_name         = var.sns_topic_name
    eventbridge_rule_name  = "${var.application_name}-schedule"
    custom_metrics_namespace = var.custom_metrics_namespace
    log_group_name         = aws_cloudwatch_log_group.application_logs.name
    aws_region            = data.aws_region.current.name
  })

  tags = var.tags
}

# CloudWatch composite alarm for overall system health
resource "aws_cloudwatch_composite_alarm" "system_health_alarm" {
  alarm_name        = "${var.application_name}-system-health"
  alarm_description = "Composite alarm for overall AI News Agent system health"

  alarm_rule = join(" OR ", [
    "ALARM(${aws_cloudwatch_metric_alarm.lambda_error_alarm.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.lambda_throttle_alarm.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.custom_error_alarm.alarm_name})",
    var.sns_topic_name != null ? "ALARM(${aws_cloudwatch_metric_alarm.sns_failure_alarm[0].alarm_name})" : ""
  ])

  alarm_actions = var.composite_alarm_actions
  ok_actions    = var.composite_ok_actions

  tags = var.tags
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}