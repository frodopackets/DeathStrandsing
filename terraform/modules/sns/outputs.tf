# Outputs for SNS topic and subscription module

output "sns_topic_arn" {
  description = "ARN of the SNS topic"
  value       = aws_sns_topic.ai_news_topic.arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic"
  value       = aws_sns_topic.ai_news_topic.name
}

output "sns_topic_id" {
  description = "ID of the SNS topic"
  value       = aws_sns_topic.ai_news_topic.id
}

output "email_subscription_rob_gmail_arn" {
  description = "ARN of the email subscription for rob.w.walker@gmail.com"
  value       = aws_sns_topic_subscription.email_subscription_rob_gmail.arn
}

output "email_subscription_rob_regions_arn" {
  description = "ARN of the email subscription for robert.walker2@regions.com"
  value       = aws_sns_topic_subscription.email_subscription_rob_regions.arn
}

output "sns_delivery_status_role_arn" {
  description = "ARN of the SNS delivery status IAM role"
  value       = aws_iam_role.sns_delivery_status_role.arn
}

output "sns_delivery_logs_group_name" {
  description = "Name of the SNS delivery status CloudWatch log group"
  value       = aws_cloudwatch_log_group.sns_delivery_logs.name
}

output "sns_delivery_logs_group_arn" {
  description = "ARN of the SNS delivery status CloudWatch log group"
  value       = aws_cloudwatch_log_group.sns_delivery_logs.arn
}