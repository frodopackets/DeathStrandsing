# EventBridge scheduler Terraform module for AI News Agent

# EventBridge rule for daily scheduling
resource "aws_cloudwatch_event_rule" "ai_news_schedule" {
  name                = var.rule_name
  description         = "Daily trigger for AI News Agent Lambda function"
  schedule_expression = var.schedule_expression
  state               = var.rule_state

  tags = var.tags
}

# EventBridge target - Lambda function
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.ai_news_schedule.name
  target_id = "AiNewsAgentLambdaTarget"
  arn       = var.lambda_function_arn

  # Dead letter queue configuration
  dead_letter_config {
    arn = aws_sqs_queue.eventbridge_dlq.arn
  }

  # Retry policy
  retry_policy {
    maximum_event_age_in_seconds = var.retry_policy.maximum_event_age_in_seconds
    maximum_retry_attempts       = var.retry_policy.maximum_retry_attempts
  }

  # Input transformer for structured input to Lambda
  input_transformer {
    input_paths = {
      "timestamp" = "$.time"
    }
    input_template = jsonencode({
      "source"    = "eventbridge.scheduler"
      "timestamp" = "<timestamp>"
      "event"     = "daily_news_summary"
    })
  }
}

# Lambda permission for EventBridge to invoke the function
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ai_news_schedule.arn
}

# Dead letter queue for failed EventBridge invocations
resource "aws_sqs_queue" "eventbridge_dlq" {
  name = "${var.rule_name}-dlq"

  # CIS-compliant settings
  kms_master_key_id                 = var.kms_key_arn
  kms_data_key_reuse_period_seconds = 300

  # Message retention
  message_retention_seconds = var.dlq_message_retention_seconds
  visibility_timeout_seconds = 300

  # Redrive policy for the DLQ itself (optional)
  redrive_policy = var.enable_dlq_redrive ? jsonencode({
    deadLetterTargetArn = aws_sqs_queue.eventbridge_dlq_redrive[0].arn
    maxReceiveCount     = var.dlq_max_receive_count
  }) : null

  tags = var.tags
}

# Optional redrive queue for the DLQ
resource "aws_sqs_queue" "eventbridge_dlq_redrive" {
  count = var.enable_dlq_redrive ? 1 : 0
  name  = "${var.rule_name}-dlq-redrive"

  # CIS-compliant settings
  kms_master_key_id                 = var.kms_key_arn
  kms_data_key_reuse_period_seconds = 300

  # Extended retention for redrive queue
  message_retention_seconds = 1209600 # 14 days

  tags = var.tags
}

# IAM role for EventBridge to access SQS DLQ
resource "aws_iam_role" "eventbridge_role" {
  name = "${var.rule_name}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for EventBridge to send messages to DLQ
resource "aws_iam_policy" "eventbridge_dlq_policy" {
  name        = "${var.rule_name}-dlq-policy"
  description = "IAM policy for EventBridge to access DLQ"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.eventbridge_dlq.arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.kms_key_arn
      }
    ]
  })

  tags = var.tags
}

# Attach policy to EventBridge role
resource "aws_iam_role_policy_attachment" "eventbridge_dlq_policy_attachment" {
  role       = aws_iam_role.eventbridge_role.name
  policy_arn = aws_iam_policy.eventbridge_dlq_policy.arn
}

# CloudWatch log group for EventBridge rule
resource "aws_cloudwatch_log_group" "eventbridge_logs" {
  name              = "/aws/events/${var.rule_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# CloudWatch metric alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages_alarm" {
  alarm_name          = "${var.rule_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "This metric monitors messages in EventBridge DLQ"
  alarm_actions       = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    QueueName = aws_sqs_queue.eventbridge_dlq.name
  }

  tags = var.tags
}