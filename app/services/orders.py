from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.db.models import Order, OrderItem


def calculate_total_price(items) -> Decimal:
    return sum(item.quantity * item.price for item in items)


async def create_order(
    session: AsyncSession,
    customer_id: UUID,
    items: list,
) -> Order:
    total_price = calculate_total_price(items)

    order = Order(
        customer_id=customer_id,
        status="NEW",
        total_price=total_price,
    )

    session.add(order)
    await session.flush()

    order_items = [
        OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price,
        )
        for item in items
    ]

    session.add_all(order_items)
    await session.commit()
    
    result = await session.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one()

    return order


async def get_order(session: AsyncSession, order_id: UUID) -> Order | None:
    result = await session.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    return result.scalar_one_or_none()
