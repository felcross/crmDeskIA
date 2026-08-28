import json
from typing import Any

import redis.asyncio as redis
import structlog

from app.config import settings

log = structlog.get_logger()


class RedisCache:
    def __init__(self):
        self._redis: redis.Redis | None = None

    async def connect(self):
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        await self._redis.ping()
        log.info("Redis connected", url=settings.redis_url)

    async def disconnect(self):
        if self._redis:
            await self._redis.close()
            log.info("Redis disconnected")

    @property
    def client(self) -> redis.Redis:
        if self._redis is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis

    async def get(self, key: str) -> Any | None:
        raw = await self.client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        serialized = json.dumps(value, default=str)
        await self.client.set(key, serialized, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await self.client.delete(*keys)
        return 0

    async def publish(self, channel: str, message: dict) -> int:
        serialized = json.dumps(message, default=str)
        return await self.client.publish(channel, serialized)

    async def subscribe(self, *channels: str):
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub


redis_cache = RedisCache()
