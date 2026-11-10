import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError

log = logging.getLogger("events")

Handler = Callable[[str, dict], Awaitable[None]]


async def publish(redis: Redis, stream: str, event_type: str, data: dict) -> str:
    return await redis.xadd(stream, {"type": event_type, "data": json.dumps(data)},
                            maxlen=10_000, approximate=True)


async def ensure_group(redis: Redis, stream: str, group: str) -> None:
    try:
        await redis.xgroup_create(stream, group, id="0", mkstream=True)
    except ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


async def consume(redis: Redis, stream: str, group: str, consumer: str, handler: Handler) -> None:
    await ensure_group(redis, stream, group)
    last_id = "0"
    while True:
        try:
            resp = await redis.xreadgroup(group, consumer, {stream: last_id}, count=10, block=5000)
        except RedisConnectionError:
            log.warning("redis connection lost, retrying in 2s")
            await asyncio.sleep(2)
            continue
        entries = resp[0][1] if resp else []
        if last_id != ">":
            if not entries:
                last_id = ">"
                continue
            last_id = entries[-1][0]
        for msg_id, fields in entries:
            try:
                await handler(fields["type"], json.loads(fields["data"]))
                await redis.xack(stream, group, msg_id)
            except Exception:
                log.exception(f"handler failed for event {msg_id}; it stays pending")
