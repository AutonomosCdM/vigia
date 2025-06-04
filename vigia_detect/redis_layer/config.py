"""Redis configuration - now using centralized settings."""

from config.settings import settings

class RedisConfig:
    """Adapter for Redis configuration from centralized settings."""
    
    def __init__(self):
        self.host = settings.redis_host
        self.port = settings.redis_port
        self.password = settings.redis_password or ""
        self.ssl = settings.redis_ssl
        
        # Semantic cache settings
        self.cache_ttl = settings.redis_cache_ttl
        self.cache_index = settings.redis_cache_index
        
        # Vector search settings  
        self.vector_index = settings.redis_vector_index
        self.vector_dim = settings.redis_vector_dim

def get_redis_config() -> RedisConfig:
    """Get Redis configuration from centralized settings."""
    return RedisConfig()
