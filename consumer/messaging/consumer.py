import json
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from consumer.core.config import settings
from consumer.db.session import AsyncSessionLocal
from consumer.services.order_processor import OrderProcessor


class OrderConsumer:
    def __init__(self):
        self._processor = OrderProcessor()

    async def start(self):
        connection = await aio_pika.connect_robust(
            settings.rabbitmq_url
        )
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            "orders", aio_pika.ExchangeType.TOPIC
        )

        queue = await channel.declare_queue(
            "order-processing",
            durable=True,
        )

        await queue.bind(exchange, routing_key="order.created")

        await queue.consume(self.handle_message)

    async def handle_message(self, message: AbstractIncomingMessage):
        async with message.process():
            payload = json.loads(message.body)
            order_id = UUID(payload["payload"]["order_id"])

            async with AsyncSessionLocal() as session:
                await self._processor.process(session, order_id)
