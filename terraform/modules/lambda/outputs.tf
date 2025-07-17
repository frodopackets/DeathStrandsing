# Outputs for Lambda function module

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.ai_news_agent.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.ai_news_agent.function_name
}

output "lambda_function_qualified_arn" {
  description = "Qualified ARN of the Lambda function"
  value       = aws_lambda_function.ai_news_agent.qualified_arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.name
}

output "lambda_dlq_arn" {
  description = "ARN of the Lambda dead letter queue"
  value       = aws_sqs_queue.lambda_dlq.arn
}

output "lambda_dlq_url" {
  description = "URL of the Lambda dead letter queue"
  value       = aws_sqs_queue.lambda_dlq.url
}

output "lambda_log_group_name" {
  description = "Name of the Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "lambda_log_group_arn" {
  description = "ARN of the Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_logs.arn
}