"""
Configuración centralizada para el proyecto Vigía
"""
import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración principal del sistema Vigía"""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Database - Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    
    # Messaging - Twilio
    twilio_account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
    twilio_whatsapp_from: str = Field(..., env="TWILIO_WHATSAPP_FROM")
    twilio_phone_from: str = Field(..., env="TWILIO_PHONE_FROM")
    
    # Messaging - Slack
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_app_token: Optional[str] = Field(None, env="SLACK_APP_TOKEN")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    slack_channel_lpp: str = Field("C08KK1SRE5S", env="SLACK_CHANNEL_LPP")
    slack_channel_vigia: str = Field("C08TJHZFVD1", env="SLACK_CHANNEL_VIGIA")
    
    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    redis_ssl: bool = Field(False, env="REDIS_SSL")
    
    # Redis Semantic Cache
    redis_cache_ttl: int = Field(3600, env="REDIS_CACHE_TTL")
    redis_cache_index: str = Field("lpp_semantic_cache", env="REDIS_CACHE_INDEX")
    
    # Redis Vector Search
    redis_vector_index: str = Field("lpp_protocols", env="REDIS_VECTOR_INDEX")
    redis_vector_dim: int = Field(768, env="REDIS_VECTOR_DIM")
    
    # AI/ML Models
    model_type: str = Field("yolov5s", env="MODEL_TYPE")
    model_confidence: float = Field(0.25, env="MODEL_CONFIDENCE")
    model_cache_dir: str = Field("./models", env="MODEL_CACHE_DIR")
    
    # Google Cloud / Vertex AI
    google_cloud_project: Optional[str] = Field(None, env="GOOGLE_CLOUD_PROJECT")
    vertex_ai_location: str = Field("us-central1", env="VERTEX_AI_LOCATION")
    
    # Server Configuration
    server_host: str = Field("0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(5000, env="SERVER_PORT")
    webhook_path: str = Field("/slack/events", env="WEBHOOK_PATH")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_hosts: list = Field(["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    # Webhook Configuration
    webhook_enabled: bool = Field(True, env="WEBHOOK_ENABLED")
    webhook_url: Optional[str] = Field(None, env="WEBHOOK_URL")
    webhook_api_key: Optional[str] = Field(None, env="WEBHOOK_API_KEY")
    webhook_timeout: int = Field(30, env="WEBHOOK_TIMEOUT")
    webhook_retry_count: int = Field(3, env="WEBHOOK_RETRY_COUNT")
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")
    
    # Processing Configuration
    use_mock_yolo: bool = Field(False, env="VIGIA_USE_MOCK_YOLO")
    yolo_model_path: str = Field("./models/yolov5s.pt", env="YOLO_MODEL_PATH")
    detection_confidence: float = Field(0.25, env="DETECTION_CONFIDENCE")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(False, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    # Anthropic API
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()
    
    @validator("model_confidence")
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Model confidence must be between 0 and 1")
        return v
    
    @validator("rate_limit_per_minute")
    def validate_rate_limit(cls, v):
        if v < 1:
            raise ValueError("Rate limit must be at least 1 per minute")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Singleton instance
settings = get_settings()