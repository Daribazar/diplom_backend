"""Redis client for caching."""
import redis.asyncio as redis
from typing import Optional
from src.config import settings


class RedisClient:
    """Redis client wrapper."""
    
    def __init__(self):
        """Initialize Redis client."""
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return await self.redis.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.redis.exists(key) > 0
    
    async def close(self):
        """Close Redis connection."""
        await self.redis.close()
