from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.db.models import Order


class OrderProcessor:
    async def process(self, session: AsyncSession, order_id: UUID) -> None:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Имитируем обработку заказа
        order.status = "PROCESSED"

        await session.commit()
