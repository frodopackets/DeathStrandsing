# Variables for CloudWatch monitoring module

variable "application_name" {
  description = "Name of the application for resource naming"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to monitor"
  type        = string
}

variable "sns_topic_name" {
  description = "Name of the SNS topic to monitor (optional)"
  type        = string
  default     = null
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}

# Log Group Configuration
variable "application_log_group_name" {
  description = "Name of the application log group"
  type        = string
}

variable "error_log_group_name" {
  description = "Name of the error log group"
  type        = string
}

variable "audit_log_group_name" {
  description = "Name of the audit log group"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days for application logs"
  type        = number
  default     = 30
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

variable "error_log_retention_days" {
  description = "CloudWatch log retention in days for error logs"
  type        = number
  default     = 90
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.error_log_retention_days)
    error_message = "Error log retention days must be a valid CloudWatch retention period."
  }
}

variable "audit_log_retention_days" {
  description = "CloudWatch log retention in days for audit logs (CIS compliance)"
  type        = number
  default     = 365
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.audit_log_retention_days)
    error_message = "Audit log retention days must be a valid CloudWatch retention period."
  }
}

# Custom Metrics Configuration
variable "custom_metrics_namespace" {
  description = "Namespace for custom CloudWatch metrics"
  type        = string
  default     = "AiNewsAgent"
}

variable "error_pattern" {
  description = "Log pattern to match for error detection"
  type        = string
  default     = "[ERROR]"
}

variable "success_pattern" {
  description = "Log pattern to match for successful executions"
  type        = string
  default     = "[SUCCESS]"
}

variable "articles_processed_pattern" {
  description = "Log pattern to match for articles processed count"
  type        = string
  default     = "[ARTICLES_PROCESSED]"
}

# Alarm Configuration - Lambda Errors
variable "error_alarm_evaluation_periods" {
  description = "Number of evaluation periods for error alarm"
  type        = number
  default     = 2
}

variable "error_alarm_period" {
  description = "Period in seconds for error alarm"
  type        = number
  default     = 300
}

variable "error_alarm_threshold" {
  description = "Threshold for error alarm"
  type        = number
  default     = 1
}

# Alarm Configuration - Lambda Duration
variable "duration_alarm_evaluation_periods" {
  description = "Number of evaluation periods for duration alarm"
  type        = number
  default     = 2
}

variable "duration_alarm_period" {
  description = "Period in seconds for duration alarm"
  type        = number
  default     = 300
}

variable "duration_alarm_threshold" {
  description = "Threshold in milliseconds for duration alarm"
  type        = number
  default     = 240000 # 4 minutes (80% of 5-minute timeout)
}

# Alarm Configuration - Lambda Throttles
variable "throttle_alarm_evaluation_periods" {
  description = "Number of evaluation periods for throttle alarm"
  type        = number
  default     = 1
}

variable "throttle_alarm_period" {
  description = "Period in seconds for throttle alarm"
  type        = number
  default     = 300
}

variable "throttle_alarm_threshold" {
  description = "Threshold for throttle alarm"
  type        = number
  default     = 0
}

# Alarm Configuration - Custom Errors
variable "custom_error_alarm_evaluation_periods" {
  description = "Number of evaluation periods for custom error alarm"
  type        = number
  default     = 2
}

variable "custom_error_alarm_period" {
  description = "Period in seconds for custom error alarm"
  type        = number
  default     = 300
}

variable "custom_error_alarm_threshold" {
  description = "Threshold for custom error alarm"
  type        = number
  default     = 1
}

# Alarm Configuration - SNS Failures
variable "sns_failure_alarm_evaluation_periods" {
  description = "Number of evaluation periods for SNS failure alarm"
  type        = number
  default     = 2
}

variable "sns_failure_alarm_period" {
  description = "Period in seconds for SNS failure alarm"
  type        = number
  default     = 300
}

variable "sns_failure_alarm_threshold" {
  description = "Threshold for SNS failure alarm"
  type        = number
  default     = 1
}

# Alarm Actions
variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of ARNs to notify when alarm returns to OK state"
  type        = list(string)
  default     = []
}

variable "composite_alarm_actions" {
  description = "List of ARNs to notify when composite alarm triggers"
  type        = list(string)
  default     = []
}

variable "composite_ok_actions" {
  description = "List of ARNs to notify when composite alarm returns to OK state"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Dashboard Configuration
variable "enable_dashboard" {
  description = "Enable CloudWatch dashboard creation"
  type        = bool
  default     = true
}

variable "dashboard_period" {
  description = "Default period for dashboard metrics in seconds"
  type        = number
  default     = 300
  
  validation {
    condition = contains([60, 300, 900, 3600, 21600, 86400], var.dashboard_period)
    error_message = "Dashboard period must be one of: 60, 300, 900, 3600, 21600, 86400 seconds."
  }
}