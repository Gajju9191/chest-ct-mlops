terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ============================================
# S3 Buckets
# ============================================
resource "aws_s3_bucket" "models" {
  bucket = var.models_bucket
  force_destroy = true

  tags = {
    Name        = "chest-ct-models"
    Environment = "production"
  }
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket = aws_s3_bucket.models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "raw_data" {
  bucket = var.raw_data_bucket
  force_destroy = true

  tags = {
    Name        = "chest-ct-raw-data"
    Environment = "production"
  }
}

resource "aws_s3_bucket_public_access_block" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================
# ECR Repository
# ============================================
resource "aws_ecr_repository" "app" {
  name = "chest-ct-api"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "chest-ct-api"
    Environment = "production"
  }
}

# ============================================
# ECS Cluster
# ============================================
resource "aws_ecs_cluster" "main" {
  name = "chest-ct-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "chest-ct-cluster"
    Environment = "production"
  }
}

# ============================================
# Task Definition
# ============================================
resource "aws_ecs_task_definition" "app" {
  family                   = "chest-ct-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "chest-ct-api"
      image = "${aws_ecr_repository.app.repository_url}:latest"
      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "MODEL_BUCKET"
          value = var.models_bucket
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/chest-ct-api"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "chest-ct-api-task"
    Environment = "production"
  }
}

# ============================================
# CloudWatch Log Group
# ============================================
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/chest-ct-api"
  retention_in_days = 30

  tags = {
    Name        = "chest-ct-api-logs"
    Environment = "production"
  }
}

# ============================================
# ECS Service
# ============================================
resource "aws_ecs_service" "app" {
  name            = "chest-ct-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "chest-ct-api"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Name        = "chest-ct-service"
    Environment = "production"
  }
}

# ============================================
# Load Balancer
# ============================================
resource "aws_lb" "main" {
  name               = "chest-ct-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb.id]
  subnets            = var.subnet_ids

  tags = {
    Name        = "chest-ct-alb"
    Environment = "production"
  }
}

resource "aws_lb_target_group" "app" {
  name        = "chest-ct-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = {
    Name        = "chest-ct-tg"
    Environment = "production"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = {
    Name        = "chest-ct-listener"
    Environment = "production"
  }
}

# ============================================
# Security Groups
# ============================================
resource "aws_security_group" "ecs_tasks" {
  name        = "chest-ct-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.lb.id]
    description     = "Allow traffic from load balancer"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "chest-ct-ecs-tasks-sg"
    Environment = "production"
  }
}

resource "aws_security_group" "lb" {
  name        = "chest-ct-lb-sg"
  description = "Security group for load balancer"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from anywhere"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "chest-ct-lb-sg"
    Environment = "production"
  }
}

# ============================================
# IAM Roles
# ============================================
resource "aws_iam_role" "ecs_task_role" {
  name = "chest-ct-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "chest-ct-ecs-task-role"
    Environment = "production"
  }
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "chest-ct-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "chest-ct-ecs-execution-role"
    Environment = "production"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_policy" "ecs_task_s3_access" {
  name        = "chest-ct-ecs-task-s3-access"
  description = "Allow ECS tasks to read models from S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.models.arn,
          "${aws_s3_bucket.models.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_s3_access" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.ecs_task_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "ecs_task_ecr_readonly" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ecs_task_cloudwatch" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# ============================================
# Data Sources
# ============================================
data "aws_caller_identity" "current" {}