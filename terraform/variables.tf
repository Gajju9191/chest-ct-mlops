variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID for deployment"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for ECS tasks"
  type        = list(string)
}

variable "task_cpu" {
  description = "CPU units for ECS task"
  type        = string
  default     = "1024"
}

variable "task_memory" {
  description = "Memory for ECS task (MB)"
  type        = string
  default     = "2048"
}

variable "desired_count" {
  description = "Number of ECS tasks"
  type        = number
  default     = 1
}

# S3 Bucket for trained models
variable "models_bucket" {
  description = "S3 bucket name for trained models"
  type        = string
  default     = "chest-ct-models-155407238004"
}

# S3 Bucket for raw training data
variable "raw_data_bucket" {
  description = "S3 bucket name for raw training data"
  type        = string
  default     = "chest-models-gajju"
}

# ✅ NEW: Secrets Manager variables
variable "dagshub_username" {
  description = "DAGsHub username for MLflow tracking"
  type        = string
  default     = "Gajju9191"
}

variable "dagshub_token" {
  description = "DAGsHub access token for MLflow tracking"
  type        = string
  sensitive   = true
}

variable "jenkins_url" {
  description = "Jenkins server URL"
  type        = string
  sensitive   = true
}

variable "jenkins_token" {
  description = "Jenkins webhook token"
  type        = string
  sensitive   = true
}

variable "jenkins_username" {
  description = "Jenkins username"
  type        = string
  default     = "Gajanan Wagalgave"
}

variable "jenkins_api_token" {
  description = "Jenkins API token"
  type        = string
  sensitive   = true
}