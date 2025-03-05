from functools import lru_cache

from redis import Redis
from redis.asyncio import Redis as AsyncRedis


@lru_cache(maxsize=1)
def get_sync_redis(connection_url: str) -> Redis:
    """Get a synchronous Redis connection, which uses a connection pool"""
    return Redis.from_url(connection_url)


@lru_cache(maxsize=1)
def get_async_redis(connection_url: str) -> AsyncRedis:
    """Get an asynchronous Redis connection, which uses a connection pool"""
    return AsyncRedis.from_url(connection_url)
