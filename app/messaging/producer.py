import json
import uuid
from datetime import datetime

import aio_pika

from app.core.config import settings


class OrderProducer:
    def __init__(self):
        self._connection = None
        self._channel = None
        self._exchange = None

    async def connect(self):
        self._connection = await aio_pika.connect_robust(
            settings.rabbitmq_url
        )
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            "orders", aio_pika.ExchangeType.TOPIC
        )

    async def publish_order_created(self, order_id, total_price):
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": "order.created",
            "occurred_at": datetime.utcnow().isoformat(),
            "payload": {
                "order_id": str(order_id),
                "total_price": str(total_price),
            },
        }

        await self._exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
            ),
            routing_key="order.created",
        )

    async def close(self):
        if self._connection:
            await self._connection.close()
