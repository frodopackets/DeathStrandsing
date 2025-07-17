# Variables for AI News Agent Terraform configuration

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ai-news-agent"
}

# Lambda Configuration
variable "lambda_memory_size" {
  description = "Memory size for Lambda function in MB"
  type        = number
  default     = 512
  
  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 MB and 10,240 MB."
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 300
  
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_concurrent_executions" {
  description = "Reserved concurrent executions for Lambda function"
  type        = number
  default     = 10
  
  validation {
    condition     = var.lambda_concurrent_executions >= 0
    error_message = "Concurrent executions must be non-negative."
  }
}

# Application Configuration
variable "search_query" {
  description = "Search query for news articles"
  type        = string
  default     = "Generative AI"
}

variable "time_range_hours" {
  description = "Time range in hours for news articles"
  type        = number
  default     = 72
  
  validation {
    condition     = var.time_range_hours > 0 && var.time_range_hours <= 168
    error_message = "Time range must be between 1 and 168 hours (1 week)."
  }
}

variable "max_articles" {
  description = "Maximum number of articles to process"
  type        = number
  default     = 50
  
  validation {
    condition     = var.max_articles > 0 && var.max_articles <= 100
    error_message = "Max articles must be between 1 and 100."
  }
}

variable "summary_length" {
  description = "Length of the summary (short, medium, long)"
  type        = string
  default     = "medium"
  
  validation {
    condition     = contains(["short", "medium", "long"], var.summary_length)
    error_message = "Summary length must be 'short', 'medium', or 'long'."
  }
}

variable "model_name" {
  description = "AI model name for summarization"
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

variable "model_provider" {
  description = "AI model provider"
  type        = string
  default     = "bedrock"
}

# SNS Configuration
variable "email_endpoints" {
  description = "List of email addresses for SNS notifications"
  type        = list(string)
  default     = [
    "rob.w.walker@gmail.com",
    "robert.walker2@regions.com"
  ]
  
  validation {
    condition     = length(var.email_endpoints) > 0
    error_message = "At least one email endpoint must be provided."
  }
}

# EventBridge Configuration
variable "schedule_expression" {
  description = "EventBridge schedule expression"
  type        = string
  default     = "rate(1 day)"
  
  validation {
    condition = can(regex("^(rate\\(.*\\)|cron\\(.*\\))$", var.schedule_expression))
    error_message = "Schedule expression must be a valid EventBridge rate or cron expression."
  }
}

# Monitoring Configuration
variable "error_threshold" {
  description = "Error threshold for CloudWatch alarms"
  type        = number
  default     = 5
  
  validation {
    condition     = var.error_threshold > 0
    error_message = "Error threshold must be greater than 0."
  }
}

variable "duration_threshold" {
  description = "Duration threshold for CloudWatch alarms in milliseconds"
  type        = number
  default     = 240000
  
  validation {
    condition     = var.duration_threshold > 0
    error_message = "Duration threshold must be greater than 0."
  }
}

# Logging Configuration
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

variable "log_level" {
  description = "Log level for the application"
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}

# Cost Monitoring Configuration
variable "monthly_budget_limit" {
  description = "Monthly budget limit in USD for the entire application"
  type        = string
  default     = "50.00"
  
  validation {
    condition     = can(tonumber(var.monthly_budget_limit))
    error_message = "Monthly budget limit must be a valid number."
  }
}

variable "lambda_budget_limit" {
  description = "Monthly budget limit in USD for Lambda costs"
  type        = string
  default     = "20.00"
  
  validation {
    condition     = can(tonumber(var.lambda_budget_limit))
    error_message = "Lambda budget limit must be a valid number."
  }
}

variable "bedrock_budget_limit" {
  description = "Monthly budget limit in USD for Bedrock AI model costs"
  type        = string
  default     = "25.00"
  
  validation {
    condition     = can(tonumber(var.bedrock_budget_limit))
    error_message = "Bedrock budget limit must be a valid number."
  }
}

variable "daily_cost_threshold" {
  description = "Daily cost threshold in USD for triggering cost alarms"
  type        = number
  default     = 5.00
  
  validation {
    condition     = var.daily_cost_threshold > 0
    error_message = "Daily cost threshold must be greater than 0."
  }
}

variable "cost_anomaly_threshold" {
  description = "Threshold in USD for cost anomaly detection"
  type        = number
  default     = 10.00
  
  validation {
    condition     = var.cost_anomaly_threshold > 0
    error_message = "Cost anomaly threshold must be greater than 0."
  }
}

variable "enable_cost_dashboard" {
  description = "Enable cost monitoring dashboard creation"
  type        = bool
  default     = true
}