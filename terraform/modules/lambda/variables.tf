# Variables for Lambda function module

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "runtime" {
  description = "Runtime for the Lambda function"
  type        = string
  default     = "python3.11"
  
  validation {
    condition = contains([
      "nodejs18.x",
      "nodejs20.x",
      "python3.9",
      "python3.10",
      "python3.11"
    ], var.runtime)
    error_message = "Runtime must be a supported Lambda runtime."
  }
}

variable "handler" {
  description = "Handler for the Lambda function"
  type        = string
  default     = "lambda_function.lambda_handler"
}

variable "memory_size" {
  description = "Memory size for the Lambda function in MB"
  type        = number
  default     = 512
  
  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "Memory size must be between 128 MB and 10,240 MB."
  }
}

variable "timeout" {
  description = "Timeout for the Lambda function in seconds"
  type        = number
  default     = 300
  
  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "sns_topic_arn" {
  description = "ARN of the SNS topic for publishing"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "reserved_concurrent_executions" {
  description = "Reserved concurrent executions for the Lambda function"
  type        = number
  default     = 10
  
  validation {
    condition     = var.reserved_concurrent_executions >= 0
    error_message = "Reserved concurrent executions must be non-negative."
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