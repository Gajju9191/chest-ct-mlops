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

variable "model_bucket" {
  description = "S3 bucket name for trained models"
  type        = string
  default     = "chest-models-gajju"
}

variable "raw_data_bucket" {
  description = "S3 bucket name for raw training data"
  type        = string
  default     = "chest-raw-data-gajju"
}