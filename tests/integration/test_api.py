import pytest
import uuid
from decimal import Decimal


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_order_valid_data(async_client, mock_order_producer):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 2,
                "price": "50.00"
            },
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "price": "30.00"
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 201
    
    data = response.json()
    assert "order_id" in data
    assert data["customer_id"] == order_data["customer_id"]
    assert data["status"] == "NEW"
    assert Decimal(data["total_price"]) == Decimal("130.00")
    assert len(data["items"]) == 2
    assert "created_at" in data
    assert "updated_at" in data
    
    # Verify producer was called
    mock_order_producer.connect.assert_called_once()
    mock_order_producer.publish_order_created.assert_called_once()
    mock_order_producer.close.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_single_item(async_client, mock_order_producer):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "price": "99.99"
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["total_price"]) == Decimal("99.99")


@pytest.mark.asyncio
async def test_create_order_invalid_quantity(async_client):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 0,  # Invalid: must be > 0
                "price": "50.00"
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_order_invalid_price(async_client):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "price": "-10.00"  # Invalid: must be > 0
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_order_invalid_customer_id(async_client):
    order_data = {
        "customer_id": "not-a-uuid",
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "price": "50.00"
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_order_saves_to_database(async_client, async_session, mock_order_producer):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "price": "100.00"
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 201
    
    data = response.json()
    order_id = uuid.UUID(data["order_id"])
    
    # Verify order exists in database
    from sqlalchemy import select
    from shared.db.models import Order
    
    result = await async_session.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    assert order is not None
    assert str(order.customer_id) == order_data["customer_id"]


@pytest.mark.asyncio
async def test_get_order_existing(async_client, async_session, mock_order_producer):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 2,
                "price": "25.00"
            }
        ]
    }
    
    create_response = await async_client.post("/orders/", json=order_data)
    assert create_response.status_code == 201
    
    order_id = create_response.json()["order_id"]
    
    get_response = await async_client.get(f"/orders/{order_id}")
    
    assert get_response.status_code == 200
    
    data = get_response.json()
    assert data["order_id"] == order_id
    assert data["customer_id"] == order_data["customer_id"]
    assert data["status"] == "NEW"
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_order_not_found(async_client):
    non_existent_id = uuid.uuid4()
    
    response = await async_client.get(f"/orders/{non_existent_id}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


@pytest.mark.asyncio
async def test_get_order_invalid_uuid(async_client):
    response = await async_client.get("/orders/not-a-uuid")
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_order_publishes_to_rabbitmq(async_client, mock_order_producer):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "price": "50.00"
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 201
    
    assert mock_order_producer.connect.called
    assert mock_order_producer.publish_order_created.called
    assert mock_order_producer.close.called
    
    call_args = mock_order_producer.publish_order_created.call_args[0]
    order_id = call_args[0]
    total_price = call_args[1]
    
    assert isinstance(order_id, uuid.UUID)
    assert total_price == Decimal("50.00")


@pytest.mark.asyncio
async def test_create_order_empty_items_list(async_client, mock_order_producer):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": []
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["total_price"]) == Decimal("0")


@pytest.mark.asyncio
async def test_order_response_structure(async_client, mock_order_producer):
    order_data = {
        "customer_id": str(uuid.uuid4()),
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "quantity": 1,
                "price": "25.50"
            }
        ]
    }
    
    response = await async_client.post("/orders/", json=order_data)
    
    assert response.status_code == 201
    
    data = response.json()
    
    required_fields = [
        "order_id", "customer_id", "status", "total_price",
        "items", "created_at", "updated_at"
    ]
    
    for field in required_fields:
        assert field in data
    
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert "product_id" in item
    assert "quantity" in item
    assert "price" in item

