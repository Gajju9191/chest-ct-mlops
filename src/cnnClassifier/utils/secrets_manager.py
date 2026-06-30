
"""
AWS Secrets Manager integration for secure credential management.
"""
import os
import json
import boto3
import logging
from functools import lru_cache
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecretsManager:
    """Secure secrets manager with caching"""
    
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region)
        self._cache = {}
        
    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve a secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                secret = json.loads(response['SecretString'])
                logger.info(f"✅ Retrieved secret: {secret_name}")
                return secret
            else:
                raise ValueError("Binary secrets not supported")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"❌ Secret {secret_name} not found")
            elif error_code == 'InvalidRequestException':
                logger.error(f"❌ Invalid request for secret {secret_name}")
            else:
                logger.error(f"❌ Error retrieving secret {secret_name}: {e}")
            raise
    
    def get_mlflow_credentials(self) -> dict:
        """Get MLflow credentials from secrets"""
        try:
            return self.get_secret('chest-ct/mlflow/credentials')
        except:
            return {
                'tracking_uri': os.environ.get('MLFLOW_TRACKING_URI'),
                'username': os.environ.get('MLFLOW_TRACKING_USERNAME'),
                'password': os.environ.get('MLFLOW_TRACKING_PASSWORD')
            }
    
    def get_s3_credentials(self) -> dict:
        """Get S3 bucket names from secrets"""
        try:
            return self.get_secret('chest-ct/s3/credentials')
        except:
            return {
                'models_bucket': os.environ.get('MODEL_BUCKET', 'chest-ct-models-155407238004'),
                'data_bucket': os.environ.get('DATA_BUCKET', 'chest-models-gajju')
            }
    
    def setup_mlflow(self):
        """Setup MLflow environment variables from secrets"""
        creds = self.get_mlflow_credentials()
        if creds:
            os.environ['MLFLOW_TRACKING_URI'] = creds.get('tracking_uri', '')
            os.environ['MLFLOW_TRACKING_USERNAME'] = creds.get('username', '')
            os.environ['MLFLOW_TRACKING_PASSWORD'] = creds.get('password', '')
            logger.info("✅ MLflow configured from Secrets Manager")
            return creds.get('tracking_uri')
        return None