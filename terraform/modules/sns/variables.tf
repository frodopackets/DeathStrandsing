# Variables for SNS topic and subscription module

variable "topic_name" {
  description = "Name of the SNS topic"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the Lambda IAM role that can publish to this topic"
  type        = string
}

variable "email_addresses" {
  description = "Email addresses for subscriptions"
  type = object({
    rob_gmail   = string
    rob_regions = string
  })
  default = {
    rob_gmail   = "rob.w.walker@gmail.com"
    rob_regions = "robert.walker2@regions.com"
  }
  
  validation {
    condition = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email_addresses.rob_gmail)) && can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email_addresses.rob_regions))
    error_message = "Email addresses must be valid email format."
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

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "enable_message_filtering" {
  description = "Enable message filtering for subscriptions"
  type        = bool
  default     = true
}

variable "retry_policy" {
  description = "Retry policy configuration for message delivery"
  type = object({
    min_delay_target      = number
    max_delay_target      = number
    num_retries          = number
    num_max_delay_retries = number
    num_min_delay_retries = number
    num_no_delay_retries  = number
    backoff_function     = string
  })
  default = {
    min_delay_target      = 20
    max_delay_target      = 20
    num_retries          = 3
    num_max_delay_retries = 0
    num_min_delay_retries = 0
    num_no_delay_retries  = 0
    backoff_function     = "linear"
  }
  
  validation {
    condition = contains(["linear", "arithmetic", "geometric", "exponential"], var.retry_policy.backoff_function)
    error_message = "Backoff function must be one of: linear, arithmetic, geometric, exponential."
  }
}