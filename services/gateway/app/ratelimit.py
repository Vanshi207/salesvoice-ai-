import time

from redis.asyncio import Redis


async def allow(redis: Redis, key: str, limit: int, window_s: int = 60) -> bool:
    minute = int(time.time() // window_s)
    bucket = f"rl:{key}:{minute}"
    count = await redis.incr(bucket)
    if count == 1:
        await redis.expire(bucket, window_s)
    return count <= limit
