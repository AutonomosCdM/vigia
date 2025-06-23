#!/usr/bin/env python3
"""Test Redis connection before running migration."""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / "vigia_detect" / ".env")

import redis

def test_redis_connection():
    """Test basic Redis connection."""
    print("Testing Redis connection...")
    
    # Get Redis config from environment
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    password = os.getenv("REDIS_PASSWORD", "")
    use_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"SSL: {use_ssl}")
    print(f"Password: {'*' * len(password) if password else 'None'}")
    
    try:
        # Create Redis client
        client = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=use_ssl,
            decode_responses=True
        )
        
        # Test connection
        if client.ping():
            print("✅ Redis connection successful!")
            
            # Get server info
            info = client.info("server")
            print(f"Redis version: {info.get('redis_version', 'Unknown')}")
            
            return True
        else:
            print("❌ Redis ping failed")
            return False
            
    except redis.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("\nMake sure:")
        print("1. Redis server is running")
        print("2. Host and port are correct")
        print("3. Password is correct")
        print("4. SSL setting matches server configuration")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)