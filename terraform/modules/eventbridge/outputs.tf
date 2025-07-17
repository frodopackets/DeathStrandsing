# Outputs for EventBridge scheduler module

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.ai_news_schedule.arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.ai_news_schedule.name
}

output "eventbridge_rule_id" {
  description = "ID of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.ai_news_schedule.id
}

output "eventbridge_target_id" {
  description = "ID of the EventBridge target"
  value       = aws_cloudwatch_event_target.lambda_target.target_id
}

output "eventbridge_dlq_arn" {
  description = "ARN of the EventBridge dead letter queue"
  value       = aws_sqs_queue.eventbridge_dlq.arn
}

output "eventbridge_dlq_url" {
  description = "URL of the EventBridge dead letter queue"
  value       = aws_sqs_queue.eventbridge_dlq.url
}

output "eventbridge_dlq_name" {
  description = "Name of the EventBridge dead letter queue"
  value       = aws_sqs_queue.eventbridge_dlq.name
}

output "eventbridge_dlq_redrive_arn" {
  description = "ARN of the EventBridge DLQ redrive queue (if enabled)"
  value       = var.enable_dlq_redrive ? aws_sqs_queue.eventbridge_dlq_redrive[0].arn : null
}

output "eventbridge_role_arn" {
  description = "ARN of the EventBridge IAM role"
  value       = aws_iam_role.eventbridge_role.arn
}

output "eventbridge_role_name" {
  description = "Name of the EventBridge IAM role"
  value       = aws_iam_role.eventbridge_role.name
}

output "eventbridge_log_group_name" {
  description = "Name of the EventBridge CloudWatch log group"
  value       = aws_cloudwatch_log_group.eventbridge_logs.name
}

output "eventbridge_log_group_arn" {
  description = "ARN of the EventBridge CloudWatch log group"
  value       = aws_cloudwatch_log_group.eventbridge_logs.arn
}

output "dlq_alarm_name" {
  description = "Name of the DLQ CloudWatch alarm"
  value       = aws_cloudwatch_metric_alarm.dlq_messages_alarm.alarm_name
}

output "dlq_alarm_arn" {
  description = "ARN of the DLQ CloudWatch alarm"
  value       = aws_cloudwatch_metric_alarm.dlq_messages_alarm.arn
}