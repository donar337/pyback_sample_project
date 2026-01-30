import pytest
import json
import uuid
from decimal import Decimal
from datetime import datetime

from app.messaging.producer import OrderProducer


@pytest.mark.asyncio
async def test_producer_connect(mock_rabbitmq):
    producer = OrderProducer()
    
    await producer.connect()
    
    assert producer._connection is not None
    assert producer._channel is not None
    assert producer._exchange is not None
    
    mock_rabbitmq['connection'].channel.assert_called_once()
    mock_rabbitmq['channel'].declare_exchange.assert_called_once()


@pytest.mark.asyncio
async def test_producer_publish_order_created(mock_rabbitmq):
    producer = OrderProducer()
    await producer.connect()
    
    order_id = uuid.uuid4()
    total_price = Decimal("150.00")
    
    await producer.publish_order_created(order_id, total_price)
    
    mock_rabbitmq['exchange'].publish.assert_called_once()
    
    call_args = mock_rabbitmq['exchange'].publish.call_args
    message = call_args[0][0]
    routing_key = call_args[1]['routing_key']
    
    assert routing_key == "order.created"
    
    body = json.loads(message.body.decode())
    assert body['event_type'] == 'order.created'
    assert body['payload']['order_id'] == str(order_id)
    assert body['payload']['total_price'] == str(total_price)
    assert 'event_id' in body
    assert 'occurred_at' in body


@pytest.mark.asyncio
async def test_producer_message_structure(mock_rabbitmq):
    producer = OrderProducer()
    await producer.connect()
    
    order_id = uuid.uuid4()
    total_price = Decimal("99.99")
    
    await producer.publish_order_created(order_id, total_price)
    
    call_args = mock_rabbitmq['exchange'].publish.call_args
    message = call_args[0][0]
    body = json.loads(message.body.decode())
    
    assert 'event_id' in body
    assert 'event_type' in body
    assert 'occurred_at' in body
    assert 'payload' in body
    
    payload = body['payload']
    assert 'order_id' in payload
    assert 'total_price' in payload
    
    uuid.UUID(body['event_id'])
    
    datetime.fromisoformat(body['occurred_at'])


@pytest.mark.asyncio
async def test_producer_serializes_uuid_and_decimal(mock_rabbitmq):
    producer = OrderProducer()
    await producer.connect()
    
    order_id = uuid.uuid4()
    total_price = Decimal("123.45")
    
    await producer.publish_order_created(order_id, total_price)
    
    call_args = mock_rabbitmq['exchange'].publish.call_args
    message = call_args[0][0]
    
    body = json.loads(message.body.decode())
    
    assert isinstance(body['payload']['order_id'], str)
    assert isinstance(body['payload']['total_price'], str)
    
    uuid.UUID(body['payload']['order_id'])
    Decimal(body['payload']['total_price'])


@pytest.mark.asyncio
async def test_producer_close(mock_rabbitmq):
    producer = OrderProducer()
    await producer.connect()
    
    await producer.close()
    
    mock_rabbitmq['connection'].close.assert_called_once()


@pytest.mark.asyncio
async def test_producer_close_without_connection(mock_rabbitmq):
    producer = OrderProducer()
    
    await producer.close()
    
    mock_rabbitmq['connection'].close.assert_not_called()


@pytest.mark.asyncio
async def test_producer_message_content_type(mock_rabbitmq):
    producer = OrderProducer()
    await producer.connect()
    
    await producer.publish_order_created(uuid.uuid4(), Decimal("50.00"))
    
    call_args = mock_rabbitmq['exchange'].publish.call_args
    message = call_args[0][0]
    
    assert message.content_type == "application/json"


@pytest.mark.asyncio
async def test_producer_exchange_declaration(mock_rabbitmq):
    producer = OrderProducer()
    await producer.connect()
    
    call_args = mock_rabbitmq['channel'].declare_exchange.call_args
    
    assert call_args[0][0] == "orders"

