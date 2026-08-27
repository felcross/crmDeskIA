import json

import structlog

from app.cache.redis_cache import redis_cache

log = structlog.get_logger()


class EventPublisher:
    """Publishes domain events via Redis Pub/Sub."""

    async def publish_lead_captured(self, lead_data: dict) -> None:
        channel = "events:lead_captured"
        subscribers = await redis_cache.publish(channel, lead_data)
        log.info("Lead captured event published", channel=channel, subscribers=subscribers)

    async def publish_notification(self, event_type: str, data: dict) -> None:
        channel = f"events:{event_type}"
        subscribers = await redis_cache.publish(channel, data)
        log.info("Event published", channel=channel, subscribers=subscribers)


event_publisher = EventPublisher()
