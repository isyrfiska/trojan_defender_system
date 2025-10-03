#!/usr/bin/env python
"""
Test Redis connectivity for Trojan Defender application.
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trojan_defender.settings')
django.setup()

from django.core.cache import cache, caches
from django.conf import settings
import redis

def test_redis_connection():
    """Test Redis connection and cache functionality."""
    print("🔍 Testing Redis Connection...")
    print("=" * 50)
    
    # Test direct Redis connection
    try:
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))
        
        print(f"📡 Connecting to Redis at {redis_host}:{redis_port}")
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            socket_connect_timeout=5
        )
        
        # Test ping
        pong = redis_client.ping()
        print(f"✅ Redis ping successful: {pong}")
        
        # Test set/get
        redis_client.set('test_direct', 'direct_value', ex=30)
        value = redis_client.get('test_direct')
        print(f"✅ Redis direct set/get: {value.decode() if value else None}")
        
    except Exception as e:
        print(f"❌ Direct Redis connection failed: {e}")
        return False
    
    # Test Django cache
    print("\n🔧 Testing Django Cache...")
    print("-" * 30)
    
    try:
        # Test default cache
        cache.set('test_django', 'django_value', 30)
        value = cache.get('test_django')
        print(f"✅ Django default cache: {value}")
        
        # Test all configured caches
        for cache_name in settings.CACHES.keys():
            try:
                cache_instance = caches[cache_name]
                test_key = f'test_{cache_name}'
                cache_instance.set(test_key, f'{cache_name}_value', 30)
                value = cache_instance.get(test_key)
                print(f"✅ Cache '{cache_name}': {value}")
            except Exception as e:
                print(f"❌ Cache '{cache_name}' failed: {e}")
        
    except Exception as e:
        print(f"❌ Django cache test failed: {e}")
        return False
    
    print("\n🎉 All Redis tests passed!")
    return True

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)