import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class RedisConfig(BaseSettings):
    """Configuration for Redis connection and operations."""
    
    host: str = Field("localhost", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    password: str = Field("", env="REDIS_PASSWORD")
    ssl: bool = Field(False, env="REDIS_SSL")
    
    # Semantic cache settings
    cache_ttl: int = Field(3600, description="TTL in seconds for cached responses")
    cache_index: str = Field("lpp_semantic_cache", description="Redis index name for semantic cache")
    
    # Vector search settings
    vector_index: str = Field("lpp_protocols", description="Redis index name for medical protocols")
    vector_dim: int = Field(768, description="Dimension of vector embeddings")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_redis_config() -> RedisConfig:
    """Get Redis configuration with environment overrides."""
    return RedisConfig()
