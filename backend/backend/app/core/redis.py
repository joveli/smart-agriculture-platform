"""
Redis 连接模块
Redis Connection Module
"""

import redis.asyncio as redis
from app.core.config import settings

redis_client: redis.Redis = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()


def get_redis() -> redis.Redis:
    return redis_client
