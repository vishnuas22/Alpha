from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    mongo_url: str = "mongodb://localhost:27017"
    db_name: str = "alpha_chatgpt"
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # JWT Configuration
    jwt_secret_key: str = "alpha-chatgpt-super-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    bcrypt_rounds: int = 12
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # File Upload
    max_file_size_mb: int = 50
    allowed_file_types: str = "image/jpeg,image/png,image/gif,image/webp,application/pdf,text/plain,text/markdown"
    
    # CORS
    allowed_origins: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Email (Optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    
    # AWS S3 (Optional)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_bucket_name: str = ""
    aws_region: str = "us-east-1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        return [file_type.strip() for file_type in self.allowed_file_types.split(",")]


settings = Settings()