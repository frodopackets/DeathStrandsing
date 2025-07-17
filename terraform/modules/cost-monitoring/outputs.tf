# Outputs for cost monitoring module

output "monthly_budget_name" {
  description = "Name of the monthly budget"
  value       = aws_budgets_budget.ai_news_agent_budget.name
}

output "lambda_budget_name" {
  description = "Name of the Lambda budget"
  value       = aws_budgets_budget.lambda_budget.name
}

output "bedrock_budget_name" {
  description = "Name of the Bedrock budget"
  value       = aws_budgets_budget.bedrock_budget.name
}

output "cost_alarm_name" {
  description = "Name of the cost alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_cost_alarm.alarm_name
}

output "cost_anomaly_detector_arn" {
  description = "ARN of the cost anomaly detector"
  value       = aws_ce_anomaly_detector.ai_news_agent_anomaly.arn
}

output "cost_anomaly_subscription_arn" {
  description = "ARN of the cost anomaly subscription"
  value       = aws_ce_anomaly_subscription.ai_news_agent_anomaly_subscription.arn
}

output "cost_dashboard_name" {
  description = "Name of the cost monitoring dashboard"
  value       = var.enable_cost_dashboard ? aws_cloudwatch_dashboard.cost_dashboard[0].dashboard_name : null
}