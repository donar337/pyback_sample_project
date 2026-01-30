import pytest
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select

from shared.db.models import Order, OrderItem


@pytest.mark.asyncio
async def test_create_order_with_attributes(async_session):
    customer_id = uuid.uuid4()
    order = Order(
        customer_id=customer_id,
        status="NEW",
        total_price=Decimal("100.50"),
    )
    
    async_session.add(order)
    await async_session.commit()
    await async_session.refresh(order)
    
    assert order.id is not None
    assert isinstance(order.id, uuid.UUID)
    assert order.customer_id == customer_id
    assert order.status == "NEW"
    assert order.total_price == Decimal("100.50")
    assert isinstance(order.created_at, datetime)
    assert isinstance(order.updated_at, datetime)


@pytest.mark.asyncio
async def test_order_uuid_generation(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("50.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    await async_session.refresh(order)
    
    assert order.id is not None
    assert isinstance(order.id, uuid.UUID)


@pytest.mark.asyncio
async def test_create_order_item_with_order(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    product_id = uuid.uuid4()
    order_item = OrderItem(
        order_id=order.id,
        product_id=product_id,
        quantity=2,
        price=Decimal("50.00"),
    )
    
    async_session.add(order_item)
    await async_session.commit()
    await async_session.refresh(order_item)
    
    assert order_item.id is not None
    assert isinstance(order_item.id, uuid.UUID)
    assert order_item.order_id == order.id
    assert order_item.product_id == product_id
    assert order_item.quantity == 2
    assert order_item.price == Decimal("50.00")


@pytest.mark.asyncio
async def test_order_items_relationship(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("150.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    item1 = OrderItem(
        order_id=order.id,
        product_id=uuid.uuid4(),
        quantity=1,
        price=Decimal("100.00"),
    )
    
    item2 = OrderItem(
        order_id=order.id,
        product_id=uuid.uuid4(),
        quantity=2,
        price=Decimal("25.00"),
    )
    
    async_session.add_all([item1, item2])
    await async_session.commit()
    
    result = await async_session.execute(
        select(Order).where(Order.id == order.id)
    )
    fetched_order = result.scalar_one()
    
    await async_session.refresh(fetched_order, ['items'])
    
    assert len(fetched_order.items) == 2
    assert all(isinstance(item, OrderItem) for item in fetched_order.items)


@pytest.mark.asyncio
async def test_cascade_delete_order_items(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    order_item = OrderItem(
        order_id=order.id,
        product_id=uuid.uuid4(),
        quantity=1,
        price=Decimal("100.00"),
    )
    
    async_session.add(order_item)
    await async_session.commit()
    
    order_id = order.id
    item_id = order_item.id
    
    await async_session.delete(order)
    await async_session.commit()
    
    result = await async_session.execute(
        select(Order).where(Order.id == order_id)
    )
    assert result.scalar_one_or_none() is None
    
    result = await async_session.execute(
        select(OrderItem).where(OrderItem.id == item_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_order_timestamp_fields(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    await async_session.refresh(order)
    
    assert order.created_at is not None
    assert order.updated_at is not None
    assert isinstance(order.created_at, datetime)
    assert isinstance(order.updated_at, datetime)
    
    time_diff = abs((order.updated_at - order.created_at).total_seconds())
    assert time_diff < 1.0

