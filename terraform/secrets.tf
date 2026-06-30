
# ============================================================
# AWS SECRETS MANAGER
# ============================================================

# MLflow Credentials
resource "aws_secretsmanager_secret" "mlflow_credentials" {
  name        = "chest-ct/mlflow/credentials"
  description = "MLflow tracking server credentials"
  
  rotation_rules {
    automatically_after_days = 30
  }
  
  tags = {
    Environment = "production"
    Project     = "chest-ct-mlops"
  }
}

resource "aws_secretsmanager_secret_version" "mlflow_credentials" {
  secret_id = aws_secretsmanager_secret.mlflow_credentials.id
  secret_string = jsonencode({
    username      = var.dagshub_username
    password      = var.dagshub_token
    tracking_uri  = "https://dagshub.com/Gajju9191/chest-ct-ecs.mlflow"
  })
}

# S3 Buckets
resource "aws_secretsmanager_secret" "s3_credentials" {
  name        = "chest-ct/s3/credentials"
  description = "S3 bucket names for models and data"
  
  tags = {
    Environment = "production"
    Project     = "chest-ct-mlops"
  }
}

resource "aws_secretsmanager_secret_version" "s3_credentials" {
  secret_id = aws_secretsmanager_secret.s3_credentials.id
  secret_string = jsonencode({
    models_bucket = var.models_bucket
    data_bucket   = var.raw_data_bucket
  })
}

# Jenkins Credentials
resource "aws_secretsmanager_secret" "jenkins_credentials" {
  name        = "chest-ct/jenkins/credentials"
  description = "Jenkins server credentials"
  
  rotation_rules {
    automatically_after_days = 30
  }
  
  tags = {
    Environment = "production"
    Project     = "chest-ct-mlops"
  }
}

resource "aws_secretsmanager_secret_version" "jenkins_credentials" {
  secret_id = aws_secretsmanager_secret.jenkins_credentials.id
  secret_string = jsonencode({
    url        = var.jenkins_url
    token      = var.jenkins_token
    username   = var.jenkins_username
    api_token  = var.jenkins_api_token
  })
}

# Deployment credentials (combined for Jenkins)
resource "aws_secretsmanager_secret" "deployment_credentials" {
  name        = "chest-ct/deployment/credentials"
  description = "Combined deployment credentials"
  
  rotation_rules {
    automatically_after_days = 30
  }
  
  tags = {
    Environment = "production"
    Project     = "chest-ct-mlops"
  }
}

resource "aws_secretsmanager_secret_version" "deployment_credentials" {
  secret_id = aws_secretsmanager_secret.deployment_credentials.id
  secret_string = jsonencode({
    models_bucket       = var.models_bucket
    aws_account_id      = data.aws_caller_identity.current.account_id
    mlflow_tracking_uri = "https://dagshub.com/Gajju9191/chest-ct-ecs.mlflow"
  })
}

# IAM Policy for ECS to access Secrets Manager
resource "aws_iam_policy" "secrets_manager_access" {
  name        = "chest-ct-ecs-secrets-access"
  description = "Allow ECS tasks to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.mlflow_credentials.arn,
          aws_secretsmanager_secret.s3_credentials.arn,
          aws_secretsmanager_secret.jenkins_credentials.arn,
          aws_secretsmanager_secret.deployment_credentials.arn
        ]
      }
    ]
  })
}

# Attach policy to ECS task role
resource "aws_iam_role_policy_attachment" "ecs_secrets_manager" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.secrets_manager_access.arn
}