"""
Redis 连接管理
"""
import redis.asyncio as redis
from app.config import settings


# 创建 Redis 客户端
redis_client = redis.from_url(
    settings.REDIS_URL,
    password=settings.REDIS_PASSWORD,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端依赖"""
    return redis_client


async def close_redis():
    """关闭 Redis 连接"""
    await redis_client.close()
