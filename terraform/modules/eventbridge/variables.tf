# Variables for EventBridge scheduler module

variable "rule_name" {
  description = "Name of the EventBridge rule"
  type        = string
}

variable "schedule_expression" {
  description = "Schedule expression for the EventBridge rule (cron or rate)"
  type        = string
  default     = "cron(0 9 * * ? *)" # Daily at 9 AM UTC
  
  validation {
    condition = can(regex("^(rate|cron)\\(.*\\)$", var.schedule_expression))
    error_message = "Schedule expression must be a valid rate() or cron() expression."
  }
}

variable "rule_state" {
  description = "State of the EventBridge rule"
  type        = string
  default     = "ENABLED"
  
  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.rule_state)
    error_message = "Rule state must be either ENABLED or DISABLED."
  }
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to invoke"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to invoke"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}

variable "retry_policy" {
  description = "Retry policy configuration for EventBridge target"
  type = object({
    maximum_event_age_in_seconds = number
    maximum_retry_attempts       = number
  })
  default = {
    maximum_event_age_in_seconds = 3600  # 1 hour
    maximum_retry_attempts       = 3
  }
  
  validation {
    condition = var.retry_policy.maximum_event_age_in_seconds >= 60 && var.retry_policy.maximum_event_age_in_seconds <= 86400
    error_message = "Maximum event age must be between 60 seconds and 24 hours (86400 seconds)."
  }
  
  validation {
    condition = var.retry_policy.maximum_retry_attempts >= 0 && var.retry_policy.maximum_retry_attempts <= 185
    error_message = "Maximum retry attempts must be between 0 and 185."
  }
}

variable "dlq_message_retention_seconds" {
  description = "Message retention period for the dead letter queue in seconds"
  type        = number
  default     = 1209600 # 14 days
  
  validation {
    condition = var.dlq_message_retention_seconds >= 60 && var.dlq_message_retention_seconds <= 1209600
    error_message = "DLQ message retention must be between 60 seconds and 14 days (1209600 seconds)."
  }
}

variable "enable_dlq_redrive" {
  description = "Enable redrive queue for the DLQ"
  type        = bool
  default     = false
}

variable "dlq_max_receive_count" {
  description = "Maximum receive count for DLQ redrive policy"
  type        = number
  default     = 3
  
  validation {
    condition = var.dlq_max_receive_count >= 1 && var.dlq_max_receive_count <= 1000
    error_message = "DLQ max receive count must be between 1 and 1000."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "input_transformer_enabled" {
  description = "Enable input transformer for EventBridge target"
  type        = bool
  default     = true
}

variable "custom_input_template" {
  description = "Custom input template for EventBridge target (JSON string)"
  type        = string
  default     = null
}