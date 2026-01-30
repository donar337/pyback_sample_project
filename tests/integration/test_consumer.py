import pytest
import json
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select

from consumer.messaging.consumer import OrderConsumer
from consumer.services.order_processor import OrderProcessor
from shared.db.models import Order


@pytest.mark.asyncio
async def test_consumer_handle_message_valid(async_session, mocker):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    
    message = AsyncMock()
    message.body = json.dumps({
        "event_id": str(uuid.uuid4()),
        "event_type": "order.created",
        "occurred_at": "2024-01-01T00:00:00",
        "payload": {
            "order_id": str(order.id),
            "total_price": "100.00"
        }
    }).encode()
    
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=None)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    message.process = MagicMock(return_value=mock_context)
    
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=async_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    mock_session_maker = MagicMock(return_value=mock_session_context)
    mocker.patch('consumer.messaging.consumer.AsyncSessionLocal', mock_session_maker)
    
    consumer = OrderConsumer()
    
    await consumer.handle_message(message)
    
    result = await async_session.execute(
        select(Order).where(Order.id == order.id)
    )
    updated_order = result.scalar_one()
    
    assert updated_order.status == "PROCESSED"


@pytest.mark.asyncio
async def test_consumer_handle_message_order_not_found(async_session, mocker):
    non_existent_id = uuid.uuid4()
    
    message = AsyncMock()
    message.body = json.dumps({
        "event_id": str(uuid.uuid4()),
        "event_type": "order.created",
        "payload": {
            "order_id": str(non_existent_id),
            "total_price": "100.00"
        }
    }).encode()
    
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=None)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    message.process = MagicMock(return_value=mock_context)
    
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=async_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    mock_session_maker = MagicMock(return_value=mock_session_context)
    mocker.patch('consumer.messaging.consumer.AsyncSessionLocal', mock_session_maker)
    
    consumer = OrderConsumer()
    
    with pytest.raises(ValueError) as exc_info:
        await consumer.handle_message(message)
    
    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_consumer_handle_message_invalid_json(async_session, mocker):
    message = AsyncMock()
    message.body = b"invalid json"
    
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=None)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    message.process = MagicMock(return_value=mock_context)
    
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=async_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    mock_session_maker = MagicMock(return_value=mock_session_context)
    mocker.patch('consumer.messaging.consumer.AsyncSessionLocal', mock_session_maker)
    
    consumer = OrderConsumer()
    
    with pytest.raises(json.JSONDecodeError):
        await consumer.handle_message(message)


@pytest.mark.asyncio
async def test_consumer_handle_message_invalid_uuid(async_session, mocker):
    message = AsyncMock()
    message.body = json.dumps({
        "event_id": str(uuid.uuid4()),
        "payload": {
            "order_id": "not-a-uuid",
            "total_price": "100.00"
        }
    }).encode()
    
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=None)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    message.process = MagicMock(return_value=mock_context)
    
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=async_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    mock_session_maker = MagicMock(return_value=mock_session_context)
    mocker.patch('consumer.messaging.consumer.AsyncSessionLocal', mock_session_maker)
    
    consumer = OrderConsumer()
    
    with pytest.raises(ValueError):
        await consumer.handle_message(message)


@pytest.mark.asyncio
async def test_order_processor_process_existing_order(async_session):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("150.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    
    processor = OrderProcessor()
    await processor.process(async_session, order.id)
    
    await async_session.refresh(order)
    
    assert order.status == "PROCESSED"


@pytest.mark.asyncio
async def test_order_processor_process_not_found(async_session):
    processor = OrderProcessor()
    non_existent_id = uuid.uuid4()
    
    with pytest.raises(ValueError) as exc_info:
        await processor.process(async_session, non_existent_id)
    
    assert str(non_existent_id) in str(exc_info.value)
    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_consumer_handle_multiple_messages(async_session, mocker):
    orders = [
        Order(
            customer_id=uuid.uuid4(),
            status="NEW",
            total_price=Decimal("100.00"),
        )
        for _ in range(3)
    ]
    
    async_session.add_all(orders)
    await async_session.commit()
    
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=async_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    mock_session_maker = MagicMock(return_value=mock_session_context)
    mocker.patch('consumer.messaging.consumer.AsyncSessionLocal', mock_session_maker)
    
    consumer = OrderConsumer()
    
    for order in orders:
        message = AsyncMock()
        message.body = json.dumps({
            "event_id": str(uuid.uuid4()),
            "payload": {
                "order_id": str(order.id),
                "total_price": "100.00"
            }
        }).encode()
        
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=None)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        message.process = MagicMock(return_value=mock_context)
        
        await consumer.handle_message(message)
    
    for order in orders:
        result = await async_session.execute(
            select(Order).where(Order.id == order.id)
        )
        updated_order = result.scalar_one()
        assert updated_order.status == "PROCESSED"


@pytest.mark.asyncio
async def test_consumer_message_processing_context_manager(async_session, mocker):
    order = Order(
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("50.00"),
    )
    
    async_session.add(order)
    await async_session.commit()
    
    message = AsyncMock()
    message.body = json.dumps({
        "event_id": str(uuid.uuid4()),
        "payload": {
            "order_id": str(order.id),
            "total_price": "50.00"
        }
    }).encode()
    
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=None)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    message.process = MagicMock(return_value=mock_context)
    
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=async_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    mock_session_maker = MagicMock(return_value=mock_session_context)
    mocker.patch('consumer.messaging.consumer.AsyncSessionLocal', mock_session_maker)
    
    consumer = OrderConsumer()
    await consumer.handle_message(message)
    
    message.process.assert_called_once()
    mock_context.__aenter__.assert_called_once()
    mock_context.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_consumer_start_connects_to_rabbitmq(mock_rabbitmq):
    mock_queue = AsyncMock()
    mock_queue.bind = AsyncMock()
    mock_queue.consume = AsyncMock()
    
    mock_rabbitmq['channel'].declare_queue = AsyncMock(return_value=mock_queue)
    
    consumer = OrderConsumer()
    await consumer.start()

    mock_rabbitmq['connection'].channel.assert_called_once()
    mock_rabbitmq['channel'].declare_exchange.assert_called_once()
    mock_rabbitmq['channel'].declare_queue.assert_called_once()
    
    mock_queue.bind.assert_called_once()
    mock_queue.consume.assert_called_once()


@pytest.mark.asyncio
async def test_consumer_queue_configuration(mock_rabbitmq):
    mock_queue = AsyncMock()
    mock_queue.bind = AsyncMock()
    mock_queue.consume = AsyncMock()
    
    mock_rabbitmq['channel'].declare_queue = AsyncMock(return_value=mock_queue)
    
    consumer = OrderConsumer()
    await consumer.start()
    
    call_args = mock_rabbitmq['channel'].declare_queue.call_args
    queue_name = call_args[0][0]
    
    assert queue_name == "order-processing"
    assert call_args[1]['durable'] == True
    
    bind_call_args = mock_queue.bind.call_args
    routing_key = bind_call_args[1]['routing_key']
    
    assert routing_key == "order.created"

