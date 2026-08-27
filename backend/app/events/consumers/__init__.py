import json

import structlog

from app.cache.redis_cache import redis_cache

log = structlog.get_logger()


class EventConsumer:
    """Base class for Redis Pub/Sub consumers."""

    def __init__(self, channel: str, consumer_name: str):
        self.channel = channel
        self.consumer_name = consumer_name

    async def start(self):
        pubsub = await redis_cache.subscribe(self.channel)
        log.info("Consumer started", channel=self.channel, consumer=self.consumer_name)

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await self.handle(data)
                except Exception as e:
                    log.error(
                        "Consumer error",
                        channel=self.channel,
                        consumer=self.consumer_name,
                        error=str(e),
                    )

    async def handle(self, data: dict):
        raise NotImplementedError


class PersistLeadConsumer(EventConsumer):
    """Persists captured leads to Postgres."""

    def __init__(self):
        super().__init__("events:lead_captured", "persist_lead")

    async def handle(self, data: dict):
        log.info("Persisting lead", email=data.get("email"))
        # Will be wired to LeadRepository in T10


class SSENotifyConsumer(EventConsumer):
    """Pushes SSE notifications to connected clients."""

    def __init__(self):
        super().__init__("events:lead_captured", "sse_notify")

    async def handle(self, data: dict):
        log.info("SSE notification", email=data.get("email"))
        # Will be wired to SSE manager in T10


class EmailConsumer(EventConsumer):
    """Sends welcome emails to new leads."""

    def __init__(self):
        super().__init__("events:lead_captured", "email")

    async def handle(self, data: dict):
        log.info("Sending welcome email", email=data.get("email"))
        # Will be wired to email service in T10
