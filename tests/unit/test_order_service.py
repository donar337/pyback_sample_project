import pytest
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.orders import calculate_total_price, create_order, get_order
from app.api.schemas import OrderItemCreate
from shared.db.models import Order, OrderItem


def test_calculate_total_price_single_item():
    items = [
        MagicMock(quantity=2, price=Decimal("50.00"))
    ]
    
    total = calculate_total_price(items)
    
    assert total == Decimal("100.00")


def test_calculate_total_price_multiple_items():
    items = [
        MagicMock(quantity=2, price=Decimal("50.00")),
        MagicMock(quantity=1, price=Decimal("30.00")),
        MagicMock(quantity=3, price=Decimal("10.00")),
    ]
    
    total = calculate_total_price(items)
    
    assert total == Decimal("160.00")  # 100 + 30 + 30


def test_calculate_total_price_empty_list():
    items = []
    
    total = calculate_total_price(items)
    
    assert total == Decimal("0")


def test_calculate_total_price_decimal_precision():
    items = [
        MagicMock(quantity=3, price=Decimal("19.99")),
    ]
    
    total = calculate_total_price(items)
    
    assert total == Decimal("59.97")


@pytest.mark.asyncio
async def test_create_order_single_item(mock_session):
    customer_id = uuid.uuid4()
    items = [
        OrderItemCreate(
            product_id=uuid.uuid4(),
            quantity=1,
            price=Decimal("100.00")
        )
    ]
    
    mock_order = Order(
        id=uuid.uuid4(),
        customer_id=customer_id,
        status="NEW",
        total_price=Decimal("100.00"),
    )
    mock_order.items = [
        OrderItem(
            id=uuid.uuid4(),
            order_id=mock_order.id,
            product_id=items[0].product_id,
            quantity=items[0].quantity,
            price=items[0].price,
        )
    ]
    
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    order = await create_order(mock_session, customer_id, items)
    
    assert order.customer_id == customer_id
    assert order.status == "NEW"
    assert order.total_price == Decimal("100.00")
    
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.add_all.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_multiple_items(mock_session):
    customer_id = uuid.uuid4()
    items = [
        OrderItemCreate(
            product_id=uuid.uuid4(),
            quantity=2,
            price=Decimal("50.00")
        ),
        OrderItemCreate(
            product_id=uuid.uuid4(),
            quantity=1,
            price=Decimal("30.00")
        ),
    ]
    
    mock_order = Order(
        id=uuid.uuid4(),
        customer_id=customer_id,
        status="NEW",
        total_price=Decimal("130.00"),
    )
    mock_order.items = []
    
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    order = await create_order(mock_session, customer_id, items)
    
    assert order.total_price == Decimal("130.00")
    
    assert mock_session.add_all.called
    call_args = mock_session.add_all.call_args[0][0]
    assert len(call_args) == 2


@pytest.mark.asyncio
async def test_create_order_correct_status(mock_session):
    customer_id = uuid.uuid4()
    items = [
        OrderItemCreate(
            product_id=uuid.uuid4(),
            quantity=1,
            price=Decimal("10.00")
        )
    ]
    
    mock_order = Order(
        id=uuid.uuid4(),
        customer_id=customer_id,
        status="NEW",
        total_price=Decimal("10.00"),
    )
    mock_order.items = []
    
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    order = await create_order(mock_session, customer_id, items)
    
    assert order.status == "NEW"


@pytest.mark.asyncio
async def test_get_order_existing(mock_session):
    order_id = uuid.uuid4()
    
    mock_order = Order(
        id=order_id,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    mock_order.items = []
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    order = await get_order(mock_session, order_id)
    
    assert order is not None
    assert order.id == order_id
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_order_not_found(mock_session):
    order_id = uuid.uuid4()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    order = await get_order(mock_session, order_id)
    
    assert order is None
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_order_loads_items(mock_session):
    order_id = uuid.uuid4()
    
    mock_order = Order(
        id=order_id,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("150.00"),
    )
    
    mock_order.items = [
        OrderItem(
            id=uuid.uuid4(),
            order_id=order_id,
            product_id=uuid.uuid4(),
            quantity=2,
            price=Decimal("75.00"),
        )
    ]
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    order = await get_order(mock_session, order_id)
    
    assert order is not None
    assert len(order.items) == 1
    assert isinstance(order.items[0], OrderItem)

