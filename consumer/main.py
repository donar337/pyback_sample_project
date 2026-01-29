import asyncio
import logging

from consumer.messaging.consumer import OrderConsumer

logging.basicConfig(level=logging.INFO)


async def main():
    consumer = OrderConsumer()
    await consumer.start()

    # consumer живёт вечно
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
