import pytest
import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.db.models import Order, OrderItem


@pytest.mark.asyncio
async def test_create_order_in_database(async_session):
    customer_id = uuid.uuid4()
    
    order = Order(
        customer_id=customer_id,
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    await async_session.refresh(order)
    
    assert order.id is not None
    assert order.customer_id == customer_id
    assert order.status == "NEW"
    assert order.total_price == Decimal("100.00")


@pytest.mark.asyncio
async def test_create_order_with_items(async_session):
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
        quantity=2,
        price=Decimal("50.00"),
    )
    
    item2 = OrderItem(
        order_id=order.id,
        product_id=uuid.uuid4(),
        quantity=1,
        price=Decimal("50.00"),
    )
    
    async_session.add_all([item1, item2])
    await async_session.commit()
    
    result = await async_session.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    fetched_order = result.scalar_one()
    
    assert len(fetched_order.items) == 2


@pytest.mark.asyncio
async def test_read_order_with_relationship(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="PROCESSED",
        total_price=Decimal("200.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    product_id = uuid.uuid4()
    item = OrderItem(
        order_id=order.id,
        product_id=product_id,
        quantity=4,
        price=Decimal("50.00"),
    )
    
    async_session.add(item)
    await async_session.commit()
    
    result = await async_session.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    fetched_order = result.scalar_one()
    
    assert len(fetched_order.items) == 1
    assert fetched_order.items[0].product_id == product_id
    assert fetched_order.items[0].quantity == 4


@pytest.mark.asyncio
async def test_cascade_delete(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    item = OrderItem(
        order_id=order.id,
        product_id=uuid.uuid4(),
        quantity=1,
        price=Decimal("100.00"),
    )
    
    async_session.add(item)
    await async_session.commit()
    
    order_id = order.id
    item_id = item.id
    
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
async def test_transaction_commit(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("50.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    
    order_id = order.id
    
    result = await async_session.execute(
        select(Order).where(Order.id == order_id)
    )
    fetched_order = result.scalar_one_or_none()
    
    assert fetched_order is not None
    assert fetched_order.id == order_id


@pytest.mark.asyncio
async def test_transaction_rollback(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("50.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    order_id = order.id
    
    await async_session.rollback()
    
    result = await async_session.execute(
        select(Order).where(Order.id == order_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_update_order_status(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    
    order.status = "PROCESSED"
    await async_session.commit()
    
    result = await async_session.execute(
        select(Order).where(Order.id == order.id)
    )
    updated_order = result.scalar_one()
    
    assert updated_order.status == "PROCESSED"


@pytest.mark.asyncio
async def test_query_order_by_customer_id(async_session):
    customer_id = uuid.uuid4()
    
    order1 = Order(
        customer_id=customer_id,
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    order2 = Order(
        customer_id=customer_id,
        status="PROCESSED",
        total_price=Decimal("200.00"),
    )
    
    order3 = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("150.00"),
    )
    
    async_session.add_all([order1, order2, order3])
    await async_session.commit()
    
    result = await async_session.execute(
        select(Order).where(Order.customer_id == customer_id)
    )
    orders = result.scalars().all()
    
    assert len(orders) == 2
    assert all(order.customer_id == customer_id for order in orders)


@pytest.mark.asyncio
async def test_multiple_items_same_order(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("300.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    items = [
        OrderItem(
            order_id=order.id,
            product_id=uuid.uuid4(),
            quantity=i + 1,
            price=Decimal("50.00"),
        )
        for i in range(5)
    ]
    
    async_session.add_all(items)
    await async_session.commit()
    
    result = await async_session.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    fetched_order = result.scalar_one()
    
    assert len(fetched_order.items) == 5


@pytest.mark.asyncio
async def test_order_item_relationship(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.flush()
    
    item = OrderItem(
        order_id=order.id,
        product_id=uuid.uuid4(),
        quantity=2,
        price=Decimal("50.00"),
    )
    
    async_session.add(item)
    await async_session.commit()
    
    result = await async_session.execute(
        select(OrderItem)
        .where(OrderItem.id == item.id)
    )
    fetched_item = result.scalar_one()
    
    await async_session.refresh(fetched_item, ['order'])
    
    assert fetched_item.order.id == order.id
    assert fetched_item.order.customer_id == order.customer_id

