# Lambda function Terraform module for AI News Agent

# IAM role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Lambda function with least-privilege access
resource "aws_iam_policy" "lambda_policy" {
  name        = "${var.function_name}-policy"
  description = "IAM policy for AI News Agent Lambda function"

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
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = var.sns_topic_arn
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-lite-v1:0",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-micro-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.kms_key_arn
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.tags
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Lambda function
resource "aws_lambda_function" "ai_news_agent" {
  function_name = var.function_name
  role         = aws_iam_role.lambda_role.arn
  handler      = var.handler
  runtime      = var.runtime
  memory_size  = var.memory_size
  timeout      = var.timeout

  # Placeholder for deployment package - will be updated during deployment
  filename         = "placeholder.zip"
  source_code_hash = filebase64sha256("placeholder.zip")

  # CIS-compliant settings
  reserved_concurrent_executions = var.reserved_concurrent_executions
  
  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      PYTHONPATH = "/var/runtime"
    })
  }

  # Encryption configuration
  kms_key_arn = var.kms_key_arn

  # VPC configuration for enhanced security (optional)
  # vpc_config {
  #   subnet_ids         = var.subnet_ids
  #   security_group_ids = var.security_group_ids
  # }

  # Dead letter queue configuration
  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  # Tracing configuration for X-Ray
  tracing_config {
    mode = "Active"
  }

  tags = var.tags

  depends_on = [
    aws_iam_role_policy_attachment.lambda_policy_attachment,
    aws_cloudwatch_log_group.lambda_logs
  ]
}

# CloudWatch log group for Lambda function
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = var.tags
}

# Dead letter queue for Lambda function
resource "aws_sqs_queue" "lambda_dlq" {
  name = "${var.function_name}-dlq"

  # CIS-compliant settings
  kms_master_key_id                 = var.kms_key_arn
  kms_data_key_reuse_period_seconds = 300

  # Message retention
  message_retention_seconds = 1209600 # 14 days

  tags = var.tags
}

# IAM policy for dead letter queue
resource "aws_iam_policy" "lambda_dlq_policy" {
  name        = "${var.function_name}-dlq-policy"
  description = "IAM policy for Lambda DLQ access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.lambda_dlq.arn
      }
    ]
  })

  tags = var.tags
}

# Attach DLQ policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_dlq_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_dlq_policy.arn
}

