# Variables for cost monitoring module

variable "application_name" {
  description = "Name of the application for resource naming"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function for cost monitoring"
  type        = string
}

# Budget Configuration
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

variable "budget_alert_emails" {
  description = "List of email addresses to receive budget alerts"
  type        = list(string)
  
  validation {
    condition     = length(var.budget_alert_emails) > 0
    error_message = "At least one email address must be provided for budget alerts."
  }
}

# Cost Alarm Configuration
variable "daily_cost_threshold" {
  description = "Daily cost threshold in USD for triggering cost alarms"
  type        = number
  default     = 5.00
  
  validation {
    condition     = var.daily_cost_threshold > 0
    error_message = "Daily cost threshold must be greater than 0."
  }
}

variable "cost_alarm_actions" {
  description = "List of ARNs to notify when cost alarm triggers"
  type        = list(string)
  default     = []
}

# Cost Anomaly Detection
variable "cost_anomaly_email" {
  description = "Email address for cost anomaly notifications"
  type        = string
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.cost_anomaly_email))
    error_message = "Cost anomaly email must be a valid email address."
  }
}

variable "anomaly_threshold" {
  description = "Threshold in USD for cost anomaly detection"
  type        = number
  default     = 10.00
  
  validation {
    condition     = var.anomaly_threshold > 0
    error_message = "Anomaly threshold must be greater than 0."
  }
}

# Dashboard Configuration
variable "enable_cost_dashboard" {
  description = "Enable cost monitoring dashboard creation"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}