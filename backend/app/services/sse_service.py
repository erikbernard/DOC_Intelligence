"""Server-Sent Events (SSE) Pub/Sub service using Redis."""

import asyncio
from datetime import datetime, timezone
import json
from typing import Any, AsyncGenerator, Dict, Optional
import redis
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import app_logger


GLOBAL_EVENTS_CHANNEL = "docintelligence:events"


def get_channel_name(persona_id: Optional[str] = None) -> str:
    """Return the Redis Pub/Sub channel (global or persona-specific)."""
    if persona_id:
        return f"persona:{persona_id}:events"
    return GLOBAL_EVENTS_CHANNEL


def publish_event(
    event_type: str,
    payload: Dict[str, Any],
    persona_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> None:
    """Publish a real-time event via synchronous Redis client (called from Celery/API)."""
    channel = get_channel_name(persona_id)
    message_data = {
        "event": event_type,
        "persona_id": persona_id or payload.get("persona_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }
    try:
        r = redis.Redis.from_url(settings.redis_connection_url)
        # Publish to persona channel if specific, and always to global channel
        r.publish(channel, json.dumps(message_data))
        if channel != GLOBAL_EVENTS_CHANNEL:
            r.publish(GLOBAL_EVENTS_CHANNEL, json.dumps(message_data))
        app_logger.info(f"Published SSE event '{event_type}' to channel '{channel}'")
    except Exception as exc:
        app_logger.warning(f"Failed to publish SSE event to Redis: {str(exc)}")


async def sse_event_generator(
    persona_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE formatted strings from Redis PubSub."""
    channel = get_channel_name(persona_id)
    r = aioredis.from_url(settings.redis_connection_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    app_logger.info(f"Subscribed client to SSE channel: {channel}")

    # Send initial connection ping
    init_event = json.dumps({"status": "connected", "channel": channel})
    yield f"event: connected\ndata: {init_event}\n\n"

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message.get("data"):
                raw_data = message["data"]
                try:
                    parsed = json.loads(raw_data)
                    event_name = parsed.get("event", "message")
                    yield f"event: {event_name}\ndata: {raw_data}\n\n"
                except Exception:
                    yield f"data: {raw_data}\n\n"
            else:
                # Send periodic keep-alive comment every few seconds
                yield ": keepalive\n\n"
                await asyncio.sleep(2.0)
    except asyncio.CancelledError:
        app_logger.info(f"SSE client disconnected from channel: {channel}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await r.close()
