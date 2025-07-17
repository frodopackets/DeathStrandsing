# SNS topic and subscription Terraform module for AI News Agent

# SNS topic with encryption
resource "aws_sns_topic" "ai_news_topic" {
  name = var.topic_name

  # CIS-compliant encryption settings
  kms_master_key_id = var.kms_key_arn

  # Delivery status logging
  delivery_policy = jsonencode({
    "http" = {
      "defaultHealthyRetryPolicy" = {
        "minDelayTarget"     = var.retry_policy.min_delay_target
        "maxDelayTarget"     = var.retry_policy.max_delay_target
        "numRetries"         = var.retry_policy.num_retries
        "numMaxDelayRetries" = var.retry_policy.num_max_delay_retries
        "numMinDelayRetries" = var.retry_policy.num_min_delay_retries
        "numNoDelayRetries"  = var.retry_policy.num_no_delay_retries
        "backoffFunction"    = var.retry_policy.backoff_function
      }
      "disableSubscriptionOverrides" = false
    }
  })

  tags = var.tags
}

# SNS topic policy for secure access
resource "aws_sns_topic_policy" "ai_news_topic_policy" {
  arn = aws_sns_topic.ai_news_topic.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "ai-news-topic-policy"
    Statement = [
      {
        Sid    = "AllowLambdaPublish"
        Effect = "Allow"
        Principal = {
          AWS = var.lambda_role_arn
        }
        Action = [
          "SNS:Publish"
        ]
        Resource = aws_sns_topic.ai_news_topic.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Sid    = "DenyInsecureConnections"
        Effect = "Deny"
        Principal = "*"
        Action = "SNS:*"
        Resource = aws_sns_topic.ai_news_topic.arn
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# Email subscription for rob.w.walker@gmail.com
resource "aws_sns_topic_subscription" "email_subscription_rob_gmail" {
  topic_arn = aws_sns_topic.ai_news_topic.arn
  protocol  = "email"
  endpoint  = var.email_addresses.rob_gmail

  # Message filtering (optional)
  filter_policy = var.enable_message_filtering ? jsonencode({
    "message_type" = ["news_summary", "error_notification"]
  }) : null

  # Delivery status logging
  delivery_policy = jsonencode({
    "healthyRetryPolicy" = {
      "minDelayTarget"     = var.retry_policy.min_delay_target
      "maxDelayTarget"     = var.retry_policy.max_delay_target
      "numRetries"         = var.retry_policy.num_retries
      "numMaxDelayRetries" = var.retry_policy.num_max_delay_retries
      "numMinDelayRetries" = var.retry_policy.num_min_delay_retries
      "numNoDelayRetries"  = var.retry_policy.num_no_delay_retries
      "backoffFunction"    = var.retry_policy.backoff_function
    }
  })
}

# Email subscription for robert.walker2@regions.com
resource "aws_sns_topic_subscription" "email_subscription_rob_regions" {
  topic_arn = aws_sns_topic.ai_news_topic.arn
  protocol  = "email"
  endpoint  = var.email_addresses.rob_regions

  # Message filtering (optional)
  filter_policy = var.enable_message_filtering ? jsonencode({
    "message_type" = ["news_summary", "error_notification"]
  }) : null

  # Delivery status logging
  delivery_policy = jsonencode({
    "healthyRetryPolicy" = {
      "minDelayTarget"     = var.retry_policy.min_delay_target
      "maxDelayTarget"     = var.retry_policy.max_delay_target
      "numRetries"         = var.retry_policy.num_retries
      "numMaxDelayRetries" = var.retry_policy.num_max_delay_retries
      "numMinDelayRetries" = var.retry_policy.num_min_delay_retries
      "numNoDelayRetries"  = var.retry_policy.num_no_delay_retries
      "backoffFunction"    = var.retry_policy.backoff_function
    }
  })
}

# CloudWatch log group for SNS delivery status
resource "aws_cloudwatch_log_group" "sns_delivery_logs" {
  name              = "/aws/sns/${var.topic_name}/delivery-status"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# IAM role for SNS delivery status logging
resource "aws_iam_role" "sns_delivery_status_role" {
  name = "${var.topic_name}-delivery-status-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for SNS delivery status logging
resource "aws_iam_policy" "sns_delivery_status_policy" {
  name        = "${var.topic_name}-delivery-status-policy"
  description = "IAM policy for SNS delivery status logging"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.sns_delivery_logs.arn}:*"
      }
    ]
  })

  tags = var.tags
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "sns_delivery_status_policy_attachment" {
  role       = aws_iam_role.sns_delivery_status_role.name
  policy_arn = aws_iam_policy.sns_delivery_status_policy.arn
}

# Data source for current AWS account ID
data "aws_caller_identity" "current" {}