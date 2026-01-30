import pytest
import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from app.api.schemas import (
    OrderItemCreate,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
)


def test_order_item_create_valid():
    item = OrderItemCreate(
        product_id=uuid.uuid4(),
        quantity=5,
        price=Decimal("99.99"),
    )
    
    assert isinstance(item.product_id, uuid.UUID)
    assert item.quantity == 5
    assert item.price == Decimal("99.99")


def test_order_item_create_quantity_validation():
    product_id = uuid.uuid4()
    
    with pytest.raises(ValidationError) as exc_info:
        OrderItemCreate(
            product_id=product_id,
            quantity=0,
            price=Decimal("10.00"),
        )
    
    assert "greater than 0" in str(exc_info.value).lower()
    
    with pytest.raises(ValidationError) as exc_info:
        OrderItemCreate(
            product_id=product_id,
            quantity=-1,
            price=Decimal("10.00"),
        )
    
    assert "greater than 0" in str(exc_info.value).lower()


def test_order_item_create_price_validation():
    product_id = uuid.uuid4()
    
    with pytest.raises(ValidationError) as exc_info:
        OrderItemCreate(
            product_id=product_id,
            quantity=1,
            price=Decimal("0.00"),
        )
    
    assert "greater than 0" in str(exc_info.value).lower()
    
    with pytest.raises(ValidationError) as exc_info:
        OrderItemCreate(
            product_id=product_id,
            quantity=1,
            price=Decimal("-10.00"),
        )
    
    assert "greater than 0" in str(exc_info.value).lower()


def test_order_create_valid():
    items = [
        OrderItemCreate(
            product_id=uuid.uuid4(),
            quantity=2,
            price=Decimal("50.00"),
        ),
        OrderItemCreate(
            product_id=uuid.uuid4(),
            quantity=1,
            price=Decimal("30.00"),
        ),
    ]
    
    order = OrderCreate(
        customer_id=uuid.uuid4(),
        items=items,
    )
    
    assert isinstance(order.customer_id, uuid.UUID)
    assert len(order.items) == 2
    assert all(isinstance(item, OrderItemCreate) for item in order.items)


def test_order_create_empty_items():
    order = OrderCreate(
        customer_id=uuid.uuid4(),
        items=[],
    )
    
    assert len(order.items) == 0


def test_order_item_response_serialization():
    item = OrderItemResponse(
        product_id=uuid.uuid4(),
        quantity=3,
        price=Decimal("25.50"),
    )
    
    assert isinstance(item.product_id, uuid.UUID)
    assert item.quantity == 3
    assert isinstance(item.price, Decimal)


def test_order_response_serialization():
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    now = datetime.utcnow()
    
    items = [
        OrderItemResponse(
            product_id=uuid.uuid4(),
            quantity=1,
            price=Decimal("100.00"),
        ),
    ]
    
    response = OrderResponse(
        order_id=order_id,
        customer_id=customer_id,
        status="NEW",
        total_price=Decimal("100.00"),
        items=items,
        created_at=now,
        updated_at=now,
    )
    
    assert response.order_id == order_id
    assert response.customer_id == customer_id
    assert response.status == "NEW"
    assert response.total_price == Decimal("100.00")
    assert len(response.items) == 1
    assert response.created_at == now
    assert response.updated_at == now


def test_order_create_uuid_type_validation():
    with pytest.raises(ValidationError):
        OrderCreate(
            customer_id="not-a-uuid",
            items=[],
        )


def test_order_item_create_uuid_type_validation():
    with pytest.raises(ValidationError):
        OrderItemCreate(
            product_id="not-a-uuid",
            quantity=1,
            price=Decimal("10.00"),
        )


def test_order_create_with_decimal_string():
    item = OrderItemCreate(
        product_id=uuid.uuid4(),
        quantity=1,
        price="19.99",
    )
    
    assert isinstance(item.price, Decimal)
    assert item.price == Decimal("19.99")


def test_order_response_types():
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    product_id = uuid.uuid4()
    now = datetime.utcnow()
    
    response = OrderResponse(
        order_id=order_id,
        customer_id=customer_id,
        status="PROCESSED",
        total_price=Decimal("123.45"),
        items=[
            OrderItemResponse(
                product_id=product_id,
                quantity=2,
                price=Decimal("61.725"),
            )
        ],
        created_at=now,
        updated_at=now,
    )
    
    assert isinstance(response.order_id, uuid.UUID)
    assert isinstance(response.customer_id, uuid.UUID)
    assert isinstance(response.status, str)
    assert isinstance(response.total_price, Decimal)
    assert isinstance(response.created_at, datetime)
    assert isinstance(response.updated_at, datetime)

