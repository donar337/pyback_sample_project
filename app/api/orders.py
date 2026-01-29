from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import OrderCreate, OrderResponse
from app.db.session import get_session
from app.services.orders import create_order, get_order
from app.messaging.producer import OrderProducer

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order_handler(
    payload: OrderCreate,
    session: AsyncSession = Depends(get_session),
):
    order = await create_order(
        session=session,
        customer_id=payload.customer_id,
        items=payload.items,
    )

    producer = OrderProducer()
    await producer.connect()
    await producer.publish_order_created(order.id, order.total_price)
    await producer.close()

    return OrderResponse(
        order_id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        total_price=order.total_price,
        items=[
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
            }
            for item in order.items
        ],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_handler(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    order = await get_order(session, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        order_id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        total_price=order.total_price,
        items=[
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
            }
            for item in order.items
        ],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
