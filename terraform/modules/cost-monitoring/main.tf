# Cost monitoring and budget alerts for AI News Agent

# Budget for overall AI News Agent costs
resource "aws_budgets_budget" "ai_news_agent_budget" {
  name         = "${var.application_name}-monthly-budget"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  time_period_start = formatdate("YYYY-MM-01_00:00", timestamp())

  cost_filters {
    tag {
      key = "Project"
      values = ["AI News Agent"]
    }
  }

  # Alert when 80% of budget is reached
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  # Alert when 100% of budget is reached
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  # Forecast alert when projected to exceed 120% of budget
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 120
    threshold_type            = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.budget_alert_emails
  }

  tags = var.tags
}

# Budget specifically for Lambda costs
resource "aws_budgets_budget" "lambda_budget" {
  name         = "${var.application_name}-lambda-budget"
  budget_type  = "COST"
  limit_amount = var.lambda_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  time_period_start = formatdate("YYYY-MM-01_00:00", timestamp())

  cost_filters {
    service = ["Amazon Elastic Compute Cloud - Compute"]
    tag {
      key = "Project"
      values = ["AI News Agent"]
    }
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 90
    threshold_type            = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  tags = var.tags
}

# Budget for Bedrock AI model usage
resource "aws_budgets_budget" "bedrock_budget" {
  name         = "${var.application_name}-bedrock-budget"
  budget_type  = "COST"
  limit_amount = var.bedrock_budget_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  time_period_start = formatdate("YYYY-MM-01_00:00", timestamp())

  cost_filters {
    service = ["Amazon Bedrock"]
    tag {
      key = "Project"
      values = ["AI News Agent"]
    }
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 75
    threshold_type            = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  tags = var.tags
}

# CloudWatch alarm for high Lambda invocation costs
resource "aws_cloudwatch_metric_alarm" "lambda_cost_alarm" {
  alarm_name          = "${var.application_name}-lambda-cost-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400  # Daily
  statistic           = "Maximum"
  threshold           = var.daily_cost_threshold
  alarm_description   = "This metric monitors daily Lambda costs"
  alarm_actions       = var.cost_alarm_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    ServiceName = "AWSLambda"
    Currency    = "USD"
  }

  tags = var.tags
}

# Cost anomaly detection
resource "aws_ce_anomaly_detector" "ai_news_agent_anomaly" {
  name         = "${var.application_name}-cost-anomaly"
  monitor_type = "DIMENSIONAL"

  specification = jsonencode({
    Dimension = "SERVICE"
    MatchOptions = ["EQUALS"]
    Values = ["Amazon Elastic Compute Cloud - Compute", "Amazon Bedrock", "Amazon Simple Notification Service"]
  })

  tags = var.tags
}

# Cost anomaly subscription
resource "aws_ce_anomaly_subscription" "ai_news_agent_anomaly_subscription" {
  name      = "${var.application_name}-anomaly-alerts"
  frequency = "DAILY"
  
  monitor_arn_list = [
    aws_ce_anomaly_detector.ai_news_agent_anomaly.arn
  ]
  
  subscriber {
    type    = "EMAIL"
    address = var.cost_anomaly_email
  }

  threshold_expression {
    and {
      dimension {
        key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
        values        = [tostring(var.anomaly_threshold)]
        match_options = ["GREATER_THAN_OR_EQUAL"]
      }
    }
  }

  tags = var.tags
}

# CloudWatch dashboard for cost monitoring
resource "aws_cloudwatch_dashboard" "cost_dashboard" {
  count = var.enable_cost_dashboard ? 1 : 0
  dashboard_name = "${var.application_name}-cost-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "ServiceName", "AWSLambda", "Currency", "USD"],
            [".", ".", ".", "Amazon Bedrock", ".", "."],
            [".", ".", ".", "Amazon Simple Notification Service", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"  # Billing metrics are only in us-east-1
          title   = "Daily Service Costs"
          period  = 86400
          stat    = "Maximum"
        }
      },
      {
        type   = "number"
        x      = 12
        y      = 0
        width  = 6
        height = 3

        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD"]
          ]
          view    = "singleValue"
          region  = "us-east-1"
          title   = "Total Monthly Cost (USD)"
          period  = 86400
          stat    = "Maximum"
        }
      },
      {
        type   = "number"
        x      = 18
        y      = 0
        width  = 6
        height = 3

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_name]
          ]
          view    = "singleValue"
          region  = data.aws_region.current.name
          title   = "Monthly Invocations"
          period  = 2592000  # 30 days
          stat    = "Sum"
        }
      }
    ]
  })

  tags = var.tags
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}